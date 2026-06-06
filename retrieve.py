"""
Milestone 4b (+ stretch) — Semantic and hybrid retrieval.

retrieve(query, k=4, mode="semantic"|"hybrid"):
  - "semantic": top-k chunks by embedding cosine similarity (ChromaDB).
  - "hybrid"  : combine semantic search with BM25 keyword search using Reciprocal
                Rank Fusion (RRF). Keyword matching catches exact terms (e.g. a
                regulation number like "61.87") that embeddings miss — see the Q4
                failure documented in the README/eval report.

Each hit is a dict: {text, source, chunk_index, distance, bm25, rrf}.
  - distance: semantic cosine distance (None if the chunk only came from BM25)
  - bm25:     BM25 score (None if the chunk only came from semantic search)
  - rrf:      fused score (hybrid mode only; None in semantic mode)

Run:  python retrieve.py            (semantic vs. hybrid on a few questions)
"""

import json
import re
from pathlib import Path

import chromadb
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

DB_PATH = "chroma_db"
COLLECTION = "unofficial_guide"
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNKS_PATH = Path("data/chunks.jsonl")
DEFAULT_K = 4
CANDIDATE_N = 20   # how many candidates each retriever contributes before fusion
RRF_K = 60         # RRF damping constant (standard default)

# --- Load shared resources once at import time -----------------------------
_model = SentenceTransformer(MODEL_NAME)
_collection = chromadb.PersistentClient(path=DB_PATH).get_collection(COLLECTION)

# BM25 keyword index over the same chunks stored in the vector store.
_records = [json.loads(line) for line in CHUNKS_PATH.open()]
_id_to_record = {r["id"]: r for r in _records}


def _tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


_bm25 = BM25Okapi([_tokenize(r["text"]) for r in _records])


# --- Individual retrievers --------------------------------------------------
def _semantic_ranked(query, n):
    """Return up to n hits ranked by cosine similarity, each with its distance."""
    q_emb = _model.encode([query], normalize_embeddings=True).tolist()
    res = _collection.query(
        query_embeddings=q_emb,
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for cid, doc, meta, dist in zip(
        res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        hits.append(
            {
                "id": cid,
                "text": doc,
                "source": meta["source"],
                "chunk_index": meta["chunk_index"],
                "distance": dist,
                "bm25": None,
                "rrf": None,
            }
        )
    return hits


def _bm25_ranked(query, n):
    """Return up to n hits ranked by BM25 keyword score."""
    scores = _bm25.get_scores(_tokenize(query))
    top = np.argsort(scores)[::-1][:n]
    hits = []
    for idx in top:
        r = _records[idx]
        hits.append(
            {
                "id": r["id"],
                "text": r["text"],
                "source": r["source"],
                "chunk_index": r["chunk_index"],
                "distance": None,
                "bm25": float(scores[idx]),
                "rrf": None,
            }
        )
    return hits


# --- Public retrieval -------------------------------------------------------
def retrieve(query, k=DEFAULT_K, mode="semantic"):
    if mode == "semantic":
        return _semantic_ranked(query, k)

    if mode != "hybrid":
        raise ValueError(f"unknown mode: {mode!r} (use 'semantic' or 'hybrid')")

    sem = _semantic_ranked(query, CANDIDATE_N)
    kw = _bm25_ranked(query, CANDIDATE_N)

    # Reciprocal Rank Fusion: sum 1/(RRF_K + rank) across both ranked lists.
    fused = {}
    for ranked in (sem, kw):
        for rank, hit in enumerate(ranked):
            entry = fused.setdefault(
                hit["id"],
                {**hit, "rrf": 0.0},
            )
            entry["rrf"] += 1.0 / (RRF_K + rank)
            # carry over whichever score each retriever provides
            if hit["distance"] is not None:
                entry["distance"] = hit["distance"]
            if hit["bm25"] is not None:
                entry["bm25"] = hit["bm25"]

    ranked = sorted(fused.values(), key=lambda h: h["rrf"], reverse=True)
    return ranked[:k]


# --- Demo -------------------------------------------------------------------
TEST_QUERIES = [
    "What are the eligibility requirements to apply for a flight instructor certificate?",
    "What are the laws of learning and what does the law of primacy mean?",
    "What must an instructor do before endorsing a student for their first solo flight?",
]


def _fmt(hit):
    if hit["rrf"] is not None:
        score = f"rrf={hit['rrf']:.4f}"
    elif hit["distance"] is not None:
        score = f"distance={hit['distance']:.3f}"
    else:
        score = f"bm25={hit['bm25']:.2f}"
    return f"{score}  {hit['source']} (chunk {hit['chunk_index']})"


def _demo():
    for q in TEST_QUERIES:
        print("\n" + "=" * 80)
        print("QUERY:", q)
        for mode in ("semantic", "hybrid"):
            print(f"\n  --- {mode} ---")
            for i, hit in enumerate(retrieve(q, k=DEFAULT_K, mode=mode), 1):
                print(f"  [{i}] {_fmt(hit)}")


if __name__ == "__main__":
    _demo()
