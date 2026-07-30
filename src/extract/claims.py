"""Claim extraction: improved heuristics + optional LLM structured JSON."""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from src.models import Claim, ClaimType, Paper
from src.extract.llm_util import get_client, llm_available

logger = logging.getLogger(__name__)

# Broader theory / mechanism / prediction cues (v0.2 — higher recall than v0.1)
THEORY_TRIGGERS = re.compile(
    r"\b("
    r"propose|proposed|proposing|hypothesis|hypothesize|hypothesized|"
    r"theory|theoretical|mechanism|mechanistic|model\s+suggest|"
    r"we\s+(propose|hypothesize|postulate|suggest|reason|argue)|"
    r"it\s+is\s+(believed|thought|proposed|hypothesized)|"
    r"putative|presumed|conjecture|suggests\s+that|indicating\s+that|"
    r"structure-activity|structure–activity|SAR\b|"
    r"correlates?\s+with|determinant\s+of|key\s+to|"
    r"facilitat(e|es|ing)|mediated\s+by|through\s+a|"
    r"remains?\s+(unknown|unclear|controversial|poorly\s+understood)|"
    r"not\s+fully\s+understood|exact\s+mechanism|"
    r"predict|expected\s+to|would\s+(lead|result|enable)"
    r")\b",
    re.IGNORECASE,
)

MECHANISM_RE = re.compile(
    r"\b(mechanism|pathway|mediated|through|via|flip-flop|phase\s+transition|"
    r"endosomal\s+escape|protonation|destabiliz)\b",
    re.IGNORECASE,
)
PREDICTION_RE = re.compile(
    r"\b(predict|expected|anticipated|would\s+(lead|result|enable)|should\s+enable)\b",
    re.IGNORECASE,
)
ASSUMPTION_RE = re.compile(
    r"\b(assume|assumption|presumed|it\s+is\s+believed|it\s+is\s+thought)\b",
    re.IGNORECASE,
)

# Domain-grounded claim patterns even without classic "we propose"
DOMAIN_CLAIM_PATTERNS = [
    re.compile(
        r".{10,180}\b(ionizable lipid|endosomal escape|protein corona|extrahepatic|"
        r"tissue[- ]specific|pKa|helper lipid|PEG-lipid)\b.{10,180}",
        re.IGNORECASE,
    ),
]


def _split_sentences(text: str) -> list[str]:
    raw = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    return [s.strip() for s in raw if len(s.strip()) > 25]


def _classify(sent: str) -> ClaimType:
    if MECHANISM_RE.search(sent):
        return ClaimType.MECHANISM
    if PREDICTION_RE.search(sent):
        return ClaimType.PREDICTION
    if ASSUMPTION_RE.search(sent):
        return ClaimType.ASSUMPTION
    return ClaimType.THEORY


def _domain_tags(sent: str) -> list[str]:
    tags: list[str] = []
    mapping = {
        "lnp": r"\b(lnp|lipid nanoparticle)\b",
        "mrna": r"\bmrna\b",
        "endosomal_escape": r"\bendosom",
        "targeting": r"\b(target|extrahepatic|tissue[- ]specific)\b",
        "pka": r"\bpka\b",
        "corona": r"\bprotein corona\b",
        "hybrid_ncrna": r"\b(ncrna|non-coding|bifunctional|hybrid nucleic|lncrna|circrna|ribozyme|rna origami)\b",
        "sirna": r"\b(sirna|rnai|gene silencing)\b",
        "gene_therapy": r"\b(crispr|cas9|cas13|gene edit|base edit|adar)\b",
        "immunogenicity": r"\b(immunogen|innate immune|tlr|reactogen|complement)\b",
    }
    low = sent.lower()
    for tag, pat in mapping.items():
        if re.search(pat, low):
            tags.append(tag)
    return tags


def extract_claims_heuristic(paper: Paper, max_per_paper: int = 8) -> list[Claim]:
    """
    Higher-recall heuristic claim extractor.
    Pulls theory/mechanism sentences + domain-salient claim-like sentences.
    """
    claims: list[Claim] = []
    text = paper.text_blob()
    if not text:
        return claims

    seen: set[str] = set()

    def _add(sent: str, conf: float) -> None:
        nonlocal claims
        if len(claims) >= max_per_paper:
            return
        quote = sent[:200]
        key = re.sub(r"\s+", " ", quote.lower())[:120]
        if key in seen:
            return
        seen.add(key)
        claims.append(
            Claim(
                paper_id=paper.id,
                claim_type=_classify(sent),
                text=sent[:500],
                quote_span=quote,
                confidence=conf,
                tags=_domain_tags(sent),
                extractor="heuristic",
            )
        )

    for sent in _split_sentences(text):
        if THEORY_TRIGGERS.search(sent):
            _add(sent, 0.55)
        elif any(p.search(sent) for p in DOMAIN_CLAIM_PATTERNS):
            # Domain-salient sentence with a claim-ish verb or gap marker
            if re.search(
                r"\b(is|are|remains?|suggest|indicate|limit|challenge|critical|major)\b",
                sent,
                re.IGNORECASE,
            ):
                _add(sent, 0.4)

    return claims


def extract_claims_llm(paper: Paper) -> list[Claim]:
    """LLM structured claim extraction; falls back to heuristic on failure."""
    if not llm_available():
        return extract_claims_heuristic(paper)

    system_msg = (
        "You extract theoretical/mechanistic claims from biomedical paper texts about "
        "nucleic acid delivery / LNPs / mRNA. "
        'Return JSON: {"claims":[{"text":str,"claim_type":"theory|mechanism|prediction|assumption|other",'
        '"confidence":0-1,"tags":[str]}]}. '
        "Only include claims explicitly stated or strongly implied. Prefer 3-8 claims."
    )
    user_text = f"Title: {paper.title}\n\nAbstract:\n{(paper.abstract or '')[:4000]}"

    try:
        client = get_client()
        model = __import__("os").environ.get("OPENAI_MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_text},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2048,
        )
        raw = resp.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        raw_claims = parsed.get("claims", parsed.get("extractions", []))
        if isinstance(raw_claims, dict):
            raw_claims = [raw_claims]
    except Exception as e:
        logger.warning("LLM claim extraction failed: %s", e)
        return extract_claims_heuristic(paper)

    claims: list[Claim] = []
    for rc in raw_claims:
        if not isinstance(rc, dict) or not rc.get("text"):
            continue
        try:
            ctype = ClaimType(rc.get("claim_type", "theory"))
        except ValueError:
            ctype = ClaimType.THEORY
        claims.append(
            Claim(
                paper_id=paper.id,
                claim_type=ctype,
                text=str(rc["text"])[:500],
                quote_span=str(rc["text"])[:200],
                confidence=float(rc.get("confidence", 0.65)),
                tags=list(rc.get("tags") or []),
                extractor="llm",
            )
        )
    if not claims:
        return extract_claims_heuristic(paper)
    return claims


def extract_claims(paper: Paper, mode: str = "heuristic") -> list[Claim]:
    if mode == "llm":
        return extract_claims_llm(paper)
    return extract_claims_heuristic(paper)
