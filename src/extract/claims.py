"""Claim extraction: structured heuristics + optional LLM JSON.

Each claim aims to expose:
  hypothesis | evidence | mechanism | assumptions | uncertainty
plus a grounded quote_span for memorization safeguards.
"""

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
HYPOTHESIS_RE = re.compile(
    r"\b(hypothes[ei]s|we\s+propose|we\s+hypothesize|postulate|conjecture)\b",
    re.IGNORECASE,
)
UNCERTAINTY_RE = re.compile(
    r"\b("
    r"remains?\s+(unknown|unclear|controversial|elusive|poorly\s+understood)|"
    r"not\s+fully\s+understood|poorly\s+characterized|limited\s+evidence|"
    r"may\b|might\b|could\b|possibly|putative|suggests?|appears?\s+to|"
    r"however|although|challenge|bottleneck|elusive"
    r")\b",
    re.IGNORECASE,
)
EVIDENCE_CUE_RE = re.compile(
    r"\b("
    r"results?\s+show|we\s+(show|demonstrate|observe|find|measured)|"
    r"\d+(\.\d+)?\s*%|significantly|increased|decreased|reduced|"
    r"in\s+vitro|in\s+vivo|experiment"
    r")\b",
    re.IGNORECASE,
)

# Absolute / overconfident language (used for structure + downstream audits)
ABSOLUTE_RE = re.compile(
    r"\b("
    r"always|never|all\s+cases|completely|entirely|definitively|"
    r"proves?\s+that|irrefutable|without\s+exception|guarantees?"
    r")\b",
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


def _best_quote_span(claim_text: str, paper_text: str, max_len: int = 200) -> Optional[str]:
    """Prefer a contiguous source span that appears in the paper."""
    blob = paper_text or ""
    if not claim_text or not blob:
        return (claim_text or "")[:max_len] or None
    ct = claim_text.strip()
    # Exact / case-insensitive containment
    if ct in blob:
        return ct[:max_len]
    low_blob = blob.lower()
    low_ct = ct.lower()
    idx = low_blob.find(low_ct[: min(80, len(low_ct))])
    if idx >= 0:
        return blob[idx : idx + min(max_len, len(ct))]
    # Longest shared sentence-ish fragment
    for sent in _split_sentences(blob):
        if len(sent) < 30:
            continue
        if sent.lower() in low_ct or low_ct[:60] in sent.lower():
            return sent[:max_len]
    return ct[:max_len]


def structure_claim_fields(
    sent: str,
    *,
    claim_type: Optional[ClaimType] = None,
    paper_context: str = "",
) -> dict:
    """Decompose a free-text claim sentence into structured slots.

    Heuristic and deterministic — used by both offline extract and audits.
    Missing slots stay None / [].
    """
    ctype = claim_type or _classify(sent)
    hypothesis: Optional[str] = None
    mechanism: Optional[str] = None
    evidence: Optional[str] = None
    assumptions: list[str] = []
    uncertainty: Optional[str] = None

    if HYPOTHESIS_RE.search(sent) or ctype in (ClaimType.THEORY, ClaimType.PREDICTION):
        hypothesis = sent[:400]
    if MECHANISM_RE.search(sent) or ctype == ClaimType.MECHANISM:
        mechanism = sent[:400]
    if ASSUMPTION_RE.search(sent) or ctype == ClaimType.ASSUMPTION:
        assumptions = [sent[:300]]
    if EVIDENCE_CUE_RE.search(sent):
        evidence = sent[:400]
    # Also pull a nearby evidence-ish sentence from paper context if available
    if not evidence and paper_context:
        for s in _split_sentences(paper_context):
            if EVIDENCE_CUE_RE.search(s) and any(
                w in s.lower() for w in re.findall(r"[a-z]{5,}", sent.lower())[:8]
            ):
                evidence = s[:400]
                break

    unc_bits: list[str] = []
    for m in UNCERTAINTY_RE.finditer(sent):
        # Capture a short window around the hedge
        start = max(0, m.start() - 20)
        end = min(len(sent), m.end() + 40)
        frag = sent[start:end].strip()
        if frag and frag not in unc_bits:
            unc_bits.append(frag)
    if unc_bits:
        uncertainty = "; ".join(unc_bits)[:400]
    elif "unknown" in sent.lower() or "unclear" in sent.lower():
        uncertainty = sent[:400]

    # If nothing structured, at least park the sentence as hypothesis
    if not any([hypothesis, mechanism, evidence, assumptions, uncertainty]):
        hypothesis = sent[:400]

    return {
        "hypothesis": hypothesis,
        "evidence": evidence,
        "mechanism": mechanism,
        "assumptions": assumptions,
        "uncertainty": uncertainty,
    }


def _confidence_for_sentence(sent: str, base: float) -> float:
    """Down-weight absolute language and up-weight hedged claims slightly."""
    conf = base
    if ABSOLUTE_RE.search(sent):
        conf = min(conf + 0.15, 0.95)  # mark as overconfident raw; audit will flag
    if UNCERTAINTY_RE.search(sent):
        conf = max(0.25, conf - 0.08)
    return round(conf, 3)


def extract_claims_heuristic(paper: Paper, max_per_paper: int = 8) -> list[Claim]:
    """
    Higher-recall heuristic claim extractor with structured slots.
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
        quote = _best_quote_span(sent, text)
        key = re.sub(r"\s+", " ", (quote or sent).lower())[:120]
        if key in seen:
            return
        seen.add(key)
        ctype = _classify(sent)
        struct = structure_claim_fields(sent, claim_type=ctype, paper_context=text)
        claims.append(
            Claim(
                paper_id=paper.id,
                claim_type=ctype,
                text=sent[:500],
                quote_span=quote,
                confidence=_confidence_for_sentence(sent, conf),
                tags=_domain_tags(sent),
                extractor="heuristic",
                hypothesis=struct["hypothesis"],
                evidence=struct["evidence"],
                mechanism=struct["mechanism"],
                assumptions=list(struct["assumptions"] or []),
                uncertainty=struct["uncertainty"],
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
        "nucleic acid delivery / LNPs / mRNA / hybrid ncRNA. "
        "Return JSON only: "
        '{"claims":[{'
        '"text":str,'
        '"claim_type":"theory|mechanism|prediction|assumption|other",'
        '"confidence":0-1,'
        '"tags":[str],'
        '"quote_span":str,'  # verbatim substring from the abstract
        '"hypothesis":str|null,'
        '"evidence":str|null,'  # in-paper support only
        '"mechanism":str|null,'
        '"assumptions":[str],'
        '"uncertainty":str|null'  # hedges / unknowns
        "}]}. "
        "Rules: (1) Only claims explicitly stated or strongly implied in the text. "
        "(2) quote_span MUST be a contiguous verbatim snippet from the abstract. "
        "(3) Do not invent citations, DOIs, years, or results absent from the text. "
        "(4) Prefer 3-8 claims. (5) Lower confidence when hedging or evidence is thin. "
        "(6) Fill structured fields when possible; leave null if not supported."
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
            max_tokens=2500,
        )
        raw = resp.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        raw_claims = parsed.get("claims", parsed.get("extractions", []))
        if isinstance(raw_claims, dict):
            raw_claims = [raw_claims]
    except Exception as e:
        logger.warning("LLM claim extraction failed: %s", e)
        return extract_claims_heuristic(paper)

    paper_text = paper.text_blob()
    claims: list[Claim] = []
    for rc in raw_claims:
        if not isinstance(rc, dict) or not rc.get("text"):
            continue
        try:
            ctype = ClaimType(rc.get("claim_type", "theory"))
        except ValueError:
            ctype = ClaimType.THEORY
        text = str(rc["text"])[:500]
        quote_raw = rc.get("quote_span") or text
        quote = _best_quote_span(str(quote_raw), paper_text)
        # Prefer model structure; backfill from heuristics when empty
        struct = structure_claim_fields(text, claim_type=ctype, paper_context=paper_text)
        hyp = rc.get("hypothesis") or struct["hypothesis"]
        evid = rc.get("evidence") or struct["evidence"]
        mech = rc.get("mechanism") or struct["mechanism"]
        assum = rc.get("assumptions")
        if not isinstance(assum, list) or not assum:
            assum = struct["assumptions"]
        unc = rc.get("uncertainty") or struct["uncertainty"]
        try:
            conf = float(rc.get("confidence", 0.65))
        except (TypeError, ValueError):
            conf = 0.65
        conf = max(0.0, min(1.0, conf))
        claims.append(
            Claim(
                paper_id=paper.id,
                claim_type=ctype,
                text=text,
                quote_span=quote,
                confidence=conf,
                tags=list(rc.get("tags") or []) or _domain_tags(text),
                extractor="llm",
                hypothesis=str(hyp)[:500] if hyp else None,
                evidence=str(evid)[:500] if evid else None,
                mechanism=str(mech)[:500] if mech else None,
                assumptions=[str(a)[:300] for a in (assum or [])][:5],
                uncertainty=str(unc)[:500] if unc else None,
            )
        )
    if not claims:
        return extract_claims_heuristic(paper)
    return claims


def extract_claims(paper: Paper, mode: str = "heuristic") -> list[Claim]:
    if mode == "llm":
        return extract_claims_llm(paper)
    return extract_claims_heuristic(paper)
