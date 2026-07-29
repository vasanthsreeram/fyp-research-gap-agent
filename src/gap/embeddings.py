"""Embedding-based claim↔evidence alignment (sentence-transformers + optional Chroma).

Falls back gracefully when heavy deps are missing so offline lexical path stays usable.
"""

from __future__ import annotations

import hashlib
import logging
import math
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional, Sequence

logger = logging.getLogger(__name__)

# Small, fast default — good enough for short claim/evidence spans.
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_DIR_NAME = "chroma_gap_index"

_MODEL = None
_MODEL_NAME: Optional[str] = None
_IMPORT_ERROR: Optional[str] = None


def embeddings_available() -> bool:
    """True if sentence-transformers (+ torch backend) can be imported."""
    try:
        import sentence_transformers  # noqa: F401
        import numpy  # noqa: F401

        return True
    except Exception as e:  # pragma: no cover - env dependent
        global _IMPORT_ERROR
        _IMPORT_ERROR = str(e)
        return False


def chroma_available() -> bool:
    try:
        import chromadb  # noqa: F401

        return True
    except Exception:
        return False


def _l2_normalize(vecs: list[list[float]]) -> list[list[float]]:
    out: list[list[float]] = []
    for v in vecs:
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        out.append([x / norm for x in v])
    return out


def get_model(model_name: str = DEFAULT_MODEL):
    """Lazy-load and cache the SentenceTransformer model."""
    global _MODEL, _MODEL_NAME
    if _MODEL is not None and _MODEL_NAME == model_name:
        return _MODEL
    if not embeddings_available():
        raise RuntimeError(
            f"sentence-transformers unavailable: {_IMPORT_ERROR or 'import failed'}"
        )
    from sentence_transformers import SentenceTransformer

    logger.info("Loading embedding model: %s", model_name)
    _MODEL = SentenceTransformer(model_name)
    _MODEL_NAME = model_name
    return _MODEL


def embed_texts(
    texts: Sequence[str],
    *,
    model_name: str = DEFAULT_MODEL,
    batch_size: int = 32,
    normalize: bool = True,
) -> list[list[float]]:
    """Embed a batch of strings → list of float vectors."""
    cleaned = [(t or "").strip() or " " for t in texts]
    model = get_model(model_name)
    # convert_to_numpy=True is default; cast to plain lists for JSON/chroma friendliness
    vectors = model.encode(
        cleaned,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
    )
    return [v.tolist() for v in vectors]


def cosine_sim(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity; assumes optional pre-normalization (still safe if not)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return float(dot / (math.sqrt(na) * math.sqrt(nb)))


def pairwise_best_matches(
    query_texts: Sequence[str],
    candidate_texts: Sequence[str],
    *,
    model_name: str = DEFAULT_MODEL,
) -> list[tuple[int, float]]:
    """
    For each query, return (best_candidate_index, cosine_sim).
    Index is -1 when candidates is empty.
    """
    if not query_texts:
        return []
    if not candidate_texts:
        return [(-1, 0.0) for _ in query_texts]

    q_vecs = embed_texts(query_texts, model_name=model_name)
    c_vecs = embed_texts(candidate_texts, model_name=model_name)

    results: list[tuple[int, float]] = []
    for qv in q_vecs:
        best_i = -1
        best_s = -1.0
        for i, cv in enumerate(c_vecs):
            s = cosine_sim(qv, cv)
            if s > best_s:
                best_s = s
                best_i = i
        results.append((best_i, max(0.0, best_s)))
    return results


def _stable_id(text: str, prefix: str = "doc") -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{h}"


def build_chroma_index(
    texts: Sequence[str],
    ids: Sequence[str],
    metadatas: Optional[Sequence[dict]] = None,
    *,
    collection_name: str = "evidence",
    persist_dir: Optional[Path] = None,
    model_name: str = DEFAULT_MODEL,
    reset: bool = True,
):
    """
    Build (or rebuild) a Chroma collection of embedded texts.
    Returns the collection, or None if chromadb is unavailable.
    """
    if not chroma_available():
        logger.warning("chromadb not installed — skipping persistent index")
        return None
    if len(texts) != len(ids):
        raise ValueError("texts and ids length mismatch")

    import chromadb
    from chromadb.config import Settings

    if persist_dir is None:
        # Default under data/processed when running from repo; else /tmp
        persist_dir = Path("data/processed") / CHROMA_DIR_NAME
    persist_dir = Path(persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )
    if reset:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine", "model": model_name},
    )

    if not texts:
        return collection

    vectors = embed_texts(list(texts), model_name=model_name)
    meta = list(metadatas) if metadatas is not None else [{"i": i} for i in range(len(texts))]
    # Chroma batch add
    collection.add(
        ids=list(ids),
        embeddings=vectors,
        documents=list(texts),
        metadatas=meta,
    )
    logger.info(
        "Chroma collection '%s' built with %d docs at %s",
        collection_name,
        len(texts),
        persist_dir,
    )
    return collection


def query_chroma(
    collection,
    query_texts: Sequence[str],
    *,
    n_results: int = 1,
    model_name: str = DEFAULT_MODEL,
) -> list[list[dict]]:
    """
    Query a Chroma collection. Returns per-query list of
    {id, document, distance, metadata, similarity} dicts.
    """
    if collection is None or not query_texts:
        return [[] for _ in query_texts]
    q_vecs = embed_texts(list(query_texts), model_name=model_name)
    raw = collection.query(
        query_embeddings=q_vecs,
        n_results=max(1, n_results),
        include=["documents", "metadatas", "distances"],
    )
    out: list[list[dict]] = []
    n_q = len(query_texts)
    ids = raw.get("ids") or [[] for _ in range(n_q)]
    docs = raw.get("documents") or [[] for _ in range(n_q)]
    metas = raw.get("metadatas") or [[] for _ in range(n_q)]
    dists = raw.get("distances") or [[] for _ in range(n_q)]
    for i in range(n_q):
        hits = []
        for j, doc_id in enumerate(ids[i] if i < len(ids) else []):
            dist = dists[i][j] if i < len(dists) and j < len(dists[i]) else 1.0
            # cosine space: distance ≈ 1 - cosine_similarity
            sim = max(0.0, 1.0 - float(dist))
            hits.append(
                {
                    "id": doc_id,
                    "document": docs[i][j] if i < len(docs) and j < len(docs[i]) else "",
                    "distance": float(dist),
                    "similarity": sim,
                    "metadata": metas[i][j] if i < len(metas) and j < len(metas[i]) else {},
                }
            )
        out.append(hits)
    return out


@lru_cache(maxsize=1)
def default_persist_dir() -> str:
    root = Path(__file__).resolve().parent.parent.parent
    return str(root / "data" / "processed" / CHROMA_DIR_NAME)
