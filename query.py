"""
Milestone 5a — Grounded answer generation.

ask(question) ties the pipeline together:
  1. retrieve the top-k chunks for the question (retrieve.py / ChromaDB),
  2. build a prompt that gives the LLM ONLY those chunks and forbids outside knowledge,
  3. call Groq's llama-3.3-70b-versatile to write the answer,
  4. attach source citations PROGRAMMATICALLY (from the retrieved chunks' metadata),
     so every answer shows where it came from regardless of what the model writes.

If the retrieved context can't answer the question, the model is instructed to say so
rather than invent a plausible-sounding answer from its training data.

Run:  python query.py     (runs a few sample questions, incl. an out-of-scope one)
"""

import os

from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve, DEFAULT_K

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
REFUSAL = "I don't have enough information on that."

SYSTEM_PROMPT = (
    "You are The Unofficial Guide, an assistant that answers questions about becoming "
    "a sport flight instructor in the United States. You must answer using ONLY the FAA "
    "source excerpts provided in the user message.\n"
    "Rules:\n"
    "1. Use only information contained in the excerpts. Do not use any outside or prior "
    "knowledge, even if you think you know the answer.\n"
    f"2. If the excerpts do not contain enough information to answer, reply with exactly: "
    f"\"{REFUSAL}\" and nothing else.\n"
    "3. Be concise and accurate. When an excerpt cites a regulation or section number "
    "(e.g., §61.183) or a handbook, include it in your answer.\n"
    "4. Do not fabricate regulation numbers, requirements, or sources."
)

_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def _build_context(hits):
    """Format retrieved chunks as a numbered context block for the prompt."""
    blocks = []
    for i, h in enumerate(hits, 1):
        blocks.append(f"[{i}] (source: {h['source']})\n{h['text']}")
    return "\n\n".join(blocks)


def ask(question, k=DEFAULT_K, mode="semantic"):
    """Return {answer, sources, hits} for a natural-language question.

    mode="semantic" uses embedding search; mode="hybrid" fuses it with BM25 keyword
    search (stretch feature). See retrieve.py.
    """
    hits = retrieve(question, k=k, mode=mode)

    if not hits:
        return {"answer": REFUSAL, "sources": [], "hits": []}

    context = _build_context(hits)
    user_msg = (
        f"Question: {question}\n\n"
        f"FAA source excerpts:\n{context}\n\n"
        "Answer the question using only the excerpts above."
    )

    completion = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,  # deterministic, factual
    )
    answer = completion.choices[0].message.content.strip()

    # Programmatic source attribution: unique source docs, in retrieval order.
    # Suppress sources when the system declined — no source supports a non-answer.
    if answer == REFUSAL:
        sources = []
    else:
        sources = list(dict.fromkeys(h["source"] for h in hits))
    return {"answer": answer, "sources": sources, "hits": hits}


def format_response(result):
    """Human-readable answer + guaranteed source list (used by CLI and reused logic)."""
    lines = [result["answer"], "", "Sources:"]
    if result["sources"]:
        lines += [f"  • {s}" for s in result["sources"]]
    else:
        lines.append("  (none)")
    return "\n".join(lines)


if __name__ == "__main__":
    samples = [
        "What are the eligibility requirements to apply for a flight instructor certificate?",
        "Can a sport pilot flight instructor train a student toward a Private Pilot certificate?",
        "What is the boiling point of water on the surface of Mars?",  # out-of-scope
    ]
    for q in samples:
        print("\n" + "=" * 80)
        print("Q:", q)
        print("-" * 80)
        print(format_response(ask(q)))
