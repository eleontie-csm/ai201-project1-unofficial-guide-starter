"""
Milestone 4b — Semantic retrieval.

Exposes retrieve(query, k=4): embed the query with the same model used to build the
index, then return the top-k most similar chunks from ChromaDB with their source and
cosine distance. Run this file directly to test retrieval on a few evaluation questions
(prints the chunks + distances so we can judge relevance before wiring in the LLM).

Run:  python retrieve.py
"""

import chromadb
from sentence_transformers import SentenceTransformer

DB_PATH = "chroma_db"
COLLECTION = "unofficial_guide"
MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_K = 4

# Load the model and collection once at import time (reused across queries).
_model = SentenceTransformer(MODEL_NAME)
_collection = chromadb.PersistentClient(path=DB_PATH).get_collection(COLLECTION)


def retrieve(query, k=DEFAULT_K):
    """Return the top-k chunks for `query` as a list of dicts:
    {text, source, chunk_index, distance}. Lower distance = more similar."""
    q_emb = _model.encode([query], normalize_embeddings=True).tolist()
    res = _collection.query(
        query_embeddings=q_emb,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        hits.append(
            {
                "text": doc,
                "source": meta["source"],
                "chunk_index": meta["chunk_index"],
                "distance": dist,
            }
        )
    return hits


# Three of the five evaluation-plan questions, spanning different source documents.
TEST_QUERIES = [
    "What are the eligibility requirements to apply for a flight instructor certificate?",
    "What are the laws of learning and what does the law of primacy mean?",
    "What must an instructor do before endorsing a student for their first solo flight?",
]


def _demo():
    for q in TEST_QUERIES:
        print("\n" + "=" * 80)
        print("QUERY:", q)
        for i, hit in enumerate(retrieve(q, k=DEFAULT_K), 1):
            print(f"\n  [{i}] distance={hit['distance']:.3f}  source={hit['source']}"
                  f"  (chunk {hit['chunk_index']})")
            snippet = " ".join(hit["text"].split())[:300]
            print(f"      {snippet}...")


if __name__ == "__main__":
    _demo()
