"""Evidence extraction: experimental results, metrics, limitations."""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from src.models import Evidence, EvidenceType, Paper
from src.extract.llm_util import get_client, llm_available

logger = logging.getLogger(__name__)

EXPERIMENT_TRIGGERS = re.compile(
    r"\b("
    r"we\s+(show|demonstrate|report|find|observe|measured|quantified)|"
    r"our\s+(results|experiments|findings)|these\s+findings|"
    r"significant(ly)?|p\s*[<=]\s*0|"
    r"fold\s+(increase|decrease|change)|efficacy|efficiency|"
    r"delivery\s+was|expression\s+was|transfection|"
    r"encapsulation|release|uptake|biodistribution|"
    r"in\s+vivo|in\s+vitro|"
    r"was\s+observed|were\s+detected|was\s+achieved|"
    r"achieved|improved|enhanced|reduced|increased\s+from|"
    r"less\s+than\s+\d|more\s+than\s+\d|\d+\s*%|\d+[-–]fold"
    r")\b",
    re.IGNORECASE,
)

LIMITATION_TRIGGERS = re.compile(
    r"\b("
    r"however|limitation|remains?\s+(unclear|challenging|unknown|poorly|controversial)|"
    r"further\s+(stud|work|investig)|"
    r"not\s+(understood|fully|achieved)|poor\s+(understanding|efficacy)|"
    r"challenge|bottleneck|barrier|limited\s+by|major\s+barrier|"
    r"suboptimal|unresolved|warrant|elusive|not\s+achieved|"
    r"must\s+be\s+improved|need\s+for\s+fundamental"
    r")\b",
    re.IGNORECASE,
)

METRIC_RE = re.compile(
    r"([\w][\w\s\-]{0,40}?)\s*(?:was|were|is|of|:|=)\s*"
    r"([<>≈~]?\s*[\d.]+\s*(?:%|fold|×|x|mg/?kg|nM|µM|uM|nm)?)",
    re.IGNORECASE,
)


def _split_sentences(text: str) -> list[str]:
    raw = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    return [s.strip() for s in raw if len(s.strip()) > 20]


def extract_evidence_heuristic(paper: Paper, max_per_paper: int = 12) -> list[Evidence]:
    """Extract experimental results, metrics, and limitations via heuristics."""
    evidences: list[Evidence] = []
    text = paper.text_blob()
    if not text:
        return evidences

    seen: set[str] = set()
    for sent in _split_sentences(text):
        if len(evidences) >= max_per_paper:
            break
        etype: Optional[EvidenceType]

        if LIMITATION_TRIGGERS.search(sent):
            etype = EvidenceType.LIMITATION
            conf = 0.55
        elif EXPERIMENT_TRIGGERS.search(sent):
            etype = EvidenceType.RESULT
            conf = 0.45
        else:
            continue

        quote = sent[:200]
        key = re.sub(r"\s+", " ", quote.lower())[:120]
        if key in seen:
            continue
        seen.add(key)

        metric_name = None
        metric_value = None
        m = METRIC_RE.search(sent)
        if m:
            metric_name = m.group(1).strip()[:60]
            metric_value = re.sub(r"\s+", " ", m.group(2).strip())[:30]
            if etype == EvidenceType.RESULT:
                etype = EvidenceType.METRIC

        tags: list[str] = []
        low = sent.lower()
        if "endosom" in low:
            tags.append("endosomal_escape")
        if "liver" in low or "hepatic" in low:
            tags.append("hepatic")
        if "in vivo" in low:
            tags.append("in_vivo")
        if "in vitro" in low:
            tags.append("in_vitro")

        evidences.append(
            Evidence(
                paper_id=paper.id,
                evidence_type=etype,
                text=sent[:500],
                quote_span=quote,
                metric_name=metric_name,
                metric_value=metric_value,
                confidence=conf,
                tags=tags,
                extractor="heuristic",
            )
        )
    return evidences


def extract_evidence_llm(paper: Paper) -> list[Evidence]:
    """LLM evidence extraction with heuristic fallback."""
    if not llm_available():
        return extract_evidence_heuristic(paper)

    system_msg = (
        "You extract experimental results, metrics, and limitations from biomedical paper texts "
        "about nucleic acid delivery / LNPs / mRNA. "
        'Return JSON: {"evidence":[{"text":str,"evidence_type":"experiment|result|metric|limitation|observation|other",'
        '"metric_name":str|null,"metric_value":str|null,"confidence":0-1,"tags":[str]}]}. Prefer 3-10 items.'
    )
    user_text = f"Title: {paper.title}\n\nAbstract:\n{(paper.abstract or '')[:4000]}"

    try:
        import os

        client = get_client()
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
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
        raw_ev = parsed.get("evidence", parsed.get("extractions", parsed.get("results", [])))
        if isinstance(raw_ev, dict):
            raw_ev = [raw_ev]
    except Exception as e:
        logger.warning("LLM evidence extraction failed: %s", e)
        return extract_evidence_heuristic(paper)

    evds: list[Evidence] = []
    for re_ in raw_ev:
        if not isinstance(re_, dict) or not re_.get("text"):
            continue
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
                confidence=float(re_.get("confidence", 0.65)),
                tags=list(re_.get("tags") or []),
                extractor="llm",
            )
        )
    if not evds:
        return extract_evidence_heuristic(paper)
    return evds


def extract_evidence(paper: Paper, mode: str = "heuristic") -> list[Evidence]:
    if mode == "llm":
        return extract_evidence_llm(paper)
    return extract_evidence_heuristic(paper)
