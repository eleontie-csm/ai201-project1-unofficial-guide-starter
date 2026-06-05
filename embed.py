"""
Milestone 4a — Embed chunks and build the vector store.

Reads the chunks produced by ingest.py (data/chunks.jsonl), embeds each one with
the all-MiniLM-L6-v2 sentence-transformer (runs locally, no API key), and stores
the vectors in a persistent ChromaDB collection with source metadata so we can
attribute answers later.

We configure the collection for COSINE distance: with normalized MiniLM embeddings,
a cosine distance near 0 means "very similar" and good matches typically score well
below 0.5 (the Milestone 4 checkpoint target).

Run:  python embed.py
"""

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path("data/chunks.jsonl")
DB_PATH = "chroma_db"
COLLECTION = "unofficial_guide"
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH = 512


def load_chunks():
    if not CHUNKS_PATH.exists():
        raise SystemExit(f"{CHUNKS_PATH} not found — run `python ingest.py` first.")
    with CHUNKS_PATH.open() as f:
        return [json.loads(line) for line in f]


def main():
    records = load_chunks()
    print(f"Loaded {len(records)} chunks from {CHUNKS_PATH}")

    print(f"Loading embedding model: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    # Fresh collection each run so re-embedding is reproducible.
    client = chromadb.PersistentClient(path=DB_PATH)
    if COLLECTION in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION)
    collection = client.create_collection(
        name=COLLECTION, metadata={"hnsw:space": "cosine"}
    )

    texts = [r["text"] for r in records]
    print("Embedding chunks (this runs on CPU and may take a minute)...")
    embeddings = model.encode(
        texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True
    )

    print("Writing to ChromaDB...")
    for i in range(0, len(records), BATCH):
        batch = records[i : i + BATCH]
        collection.add(
            ids=[r["id"] for r in batch],
            documents=[r["text"] for r in batch],
            metadatas=[
                {"source": r["source"], "chunk_index": r["chunk_index"]} for r in batch
            ],
            embeddings=embeddings[i : i + BATCH].tolist(),
        )

    print(f"\nDone. Collection '{COLLECTION}' now holds {collection.count()} vectors "
          f"at {DB_PATH}/")


if __name__ == "__main__":
    main()
