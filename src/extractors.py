"""Extractors: claims + evidence from paper text (LLM + heuristic fallback)."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from src.models import Claim, ClaimType, Evidence, EvidenceType, Paper

logger = logging.getLogger(__name__)

# ── Heuristic extractors (always work, no API key) ──────────────────────

# Terms that suggest theoretical / mechanistic claims
THEORY_TRIGGERS = re.compile(
    r"\b(propose|hypothesize|theory|mechanism|model\b.*\bsuggest|"
    r"we\s+(propose|hypothesize|postulate)|"
    r"hypothesized\s+that|proposed\s+mechanism|"
    r"theoretical\s+framework|theorize|"
    r"it\s+is\s+believed|it\s+is\s+thought|"
    r"putative|presumed|conjecture)\b",
    re.IGNORECASE,
)

# Terms suggesting experimental results/metrics
EXPERIMENT_TRIGGERS = re.compile(
    r"\b(we\s+(show|demonstrate|report|find|observe)|"
    r"our\s+results|these\s+findings|"
    r"significant(ly)?|p\s*<|p\s*=|"
    r"fold\s+increase|efficacy|efficiency|"
    r"delivery\s+was|expression\s+was|"
    r"encapsulation|release|uptake|"
    r"in\s+vivo|in\s+vitro|"
    r"was\s+observed|were\s+detected|"
    r"achieved|improved|enhanced|reduced)\b",
    re.IGNORECASE,
)

# Terms signaling limitations
LIMITATION_TRIGGERS = re.compile(
    r"\b(however|limitation|remains\s+(unclear|challenging|unknown)|"
    r"further\s+(stud|work|investig)|"
    r"not\s+understood|poor\s+(understanding|efficacy)|"
    r"challenge|bottleneck|barrier|limited\s+by|"
    r"suboptimal|unresolved|warrant)\b",
    re.IGNORECASE,
)


def _split_sentences(text: str) -> list[str]:
    """Simple sentence splitter (avoids nltk dependency)."""
    # Split on period/!/? followed by space or newline
    raw = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in raw if len(s.strip()) > 20]


def extract_claims_heuristic(paper: Paper) -> list[Claim]:
    """Extract theory/mechanism/claim sentences using heuristics."""
    claims: list[Claim] = []
    text = paper.text_blob()
    if not text:
        return claims
    seen_spans: set[str] = set()
    for sent in _split_sentences(text):
        if THEORY_TRIGGERS.search(sent):
            quote = sent[:200]
            if quote in seen_spans:
                continue
            seen_spans.add(quote)
            # Classify claim type
            ctype = ClaimType.THEORY
            if re.search(r"\b(mechanism|pathway|mediated|through|via)\b", sent, re.IGNORECASE):
                ctype = ClaimType.MECHANISM
            elif re.search(r"\b(predict|expected|anticipated|would\s+(lead|result))\b", sent, re.IGNORECASE):
                ctype = ClaimType.PREDICTION
            claims.append(
                Claim(
                    paper_id=paper.id,
                    claim_type=ctype,
                    text=sent[:500],
                    quote_span=quote,
                    confidence=0.4,
                    tags=[],
                    extractor="heuristic",
                )
            )
    return claims


def extract_evidence_heuristic(paper: Paper) -> list[Evidence]:
    """Extract experimental results, metrics, and limitations."""
    evidences: list[Evidence] = []
    text = paper.text_blob()
    if not text:
        return evidences
    seen_spans: set[str] = set()
    for sent in _split_sentences(text):
        etype = EvidenceType.RESULT
        if LIMITATION_TRIGGERS.search(sent):
            etype = EvidenceType.LIMITATION
        elif EXPERIMENT_TRIGGERS.search(sent):
            etype = EvidenceType.RESULT
        else:
            continue
        quote = sent[:200]
        if quote in seen_spans:
            continue
        seen_spans.add(quote)

        # Try to extract metric values like "85%", "3.2-fold", "p < 0.01"
        metric_name = None
        metric_value = None
        m = re.search(r"(\w[\w\s]{0,30}?)\s*(?:was|were|is|:|=)\s*([\d.]+[\d.%×\-\u00b1]*)", sent)
        if m:
            metric_name = m.group(1).strip()[:60]
            metric_value = m.group(2).strip()[:30]

        evidences.append(
            Evidence(
                paper_id=paper.id,
                evidence_type=etype,
                text=sent[:500],
                quote_span=quote,
                metric_name=metric_name,
                metric_value=metric_value,
                confidence=0.3,
                tags=[],
                extractor="heuristic",
            )
        )
    return evidences


# ── LLM extractor (if OPENAI_API_KEY available) ─────────────────────────

_LLM_AVAILABLE: Optional[bool] = None


def _llm_available() -> bool:
    global _LLM_AVAILABLE
    if _LLM_AVAILABLE is not None:
        return _LLM_AVAILABLE
    try:
        from openai import OpenAI
        key = os.environ.get("OPENAI_API_KEY")
        if key:
            # quick check
            client = OpenAI(api_key=key, timeout=5)
            client.models.list()
            _LLM_AVAILABLE = True
        else:
            _LLM_AVAILABLE = False
    except Exception:
        _LLM_AVAILABLE = False
    return _LLM_AVAILABLE


def extract_claims_llm(paper: Paper) -> list[Claim]:
    """Use LLM to extract structured claims from paper text."""
    if not _llm_available():
        logger.info("LLM not available, falling back to heuristic claims")
        return extract_claims_heuristic(paper)

    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    system_msg = (
        "You extract theoretical/mechanistic claims from biomedical paper texts. "
        "Return a JSON array of objects with keys: text, claim_type (theory|mechanism|prediction|assumption|other), confidence (0-1), tags (list of strings). "
        "Only include claims explicitly stated or strongly implied."
    )

    user_text = f"Title: {paper.title}\n\nAbstract:\n{paper.abstract[:4000]}"

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
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
        raw_claims = parsed.get("claims", parsed.get("extractions", [parsed]))
        if isinstance(raw_claims, dict):
            raw_claims = [raw_claims]
    except Exception as e:
        logger.warning("LLM claim extraction failed: %s", e)
        return extract_claims_heuristic(paper)

    claims: list[Claim] = []
    for rc in raw_claims:
        if isinstance(rc, dict) and rc.get("text"):
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
                    confidence=float(rc.get("confidence", 0.6)),
                    tags=rc.get("tags", []),
                    extractor="llm",
                )
            )
    return claims


def extract_evidence_llm(paper: Paper) -> list[Evidence]:
    """Use LLM to extract experimental evidence/results from paper."""
    if not _llm_available():
        logger.info("LLM not available, falling back to heuristic evidence")
        return extract_evidence_heuristic(paper)

    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    system_msg = (
        "You extract experimental results, metrics, and limitations from biomedical paper texts. "
        "Return a JSON array of objects with keys: text, evidence_type (experiment|result|metric|limitation|observation|other), "
        "metric_name (optional), metric_value (optional), confidence (0-1), tags (list of strings)."
    )

    user_text = f"Title: {paper.title}\n\nAbstract:\n{paper.abstract[:4000]}"

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
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
        raw_evidences = parsed.get("evidence", parsed.get("extractions", parsed.get("results", [parsed])))
        if isinstance(raw_evidences, dict):
            raw_evidences = [raw_evidences]
    except Exception as e:
        logger.warning("LLM evidence extraction failed: %s", e)
        return extract_evidence_heuristic(paper)

    evds: list[Evidence] = []
    for re_ in raw_evidences:
        if isinstance(re_, dict) and re_.get("text"):
            try:
                etype = EvidenceType(re_.get("evidence_type", "result"))
            except ValueError:
                etype = EvidenceType.RESULT
            evds.append(
                Evidence(
                    paper_id=paper.id,
                    evidence_type=etype,
                    text=str(re_["text"])[:500],
                    quote_span=str(re_["text"])[:200],
                    metric_name=(str(re_.get("metric_name") or "")[:60] or None),
                    metric_value=(str(re_.get("metric_value") or "")[:30] or None),
                    confidence=float(re_.get("confidence", 0.6)),
                    tags=re_.get("tags", []),
                    extractor="llm",
                )
            )
    return evds


# ── Unified dispatch ─────────────────────────────────────────────────

def extract_all(
    papers: list[Paper], mode: str = "auto"
) -> tuple[list[Claim], list[Evidence]]:
    """Run extraction on all papers.  mode = 'heuristic' | 'llm' | 'auto'."""
    if mode == "auto":
        mode = "llm" if _llm_available() else "heuristic"
    logger.info("Extraction mode: %s", mode)

    all_claims: list[Claim] = []
    all_evidence: list[Evidence] = []

    claim_fn = extract_claims_llm if mode == "llm" else extract_claims_heuristic
    evid_fn = extract_evidence_llm if mode == "llm" else extract_evidence_heuristic

    for paper in papers:
        try:
            claims = claim_fn(paper)
            evds = evid_fn(paper)
            all_claims.extend(claims)
            all_evidence.extend(evds)
        except Exception as e:
            logger.warning("Extraction failed for paper %s: %s", paper.title[:40], e)

    logger.info(
        "Extracted %d claims, %d evidence items from %d papers",
        len(all_claims),
        len(all_evidence),
        len(papers),
    )
    return all_claims, all_evidence
