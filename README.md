# The Unofficial Guide — Project 1

A Retrieval-Augmented Generation (RAG) system that answers plain-language questions about
**becoming a Flight Instructor with a Sport Pilot rating (CFI-S)** in the United States,
grounded in official FAA documents with source citations on every answer.

## How to run

```bash
source .venv/bin/activate
pip install -r requirements.txt

python ingest.py     # 1. load + clean + chunk the 10 PDFs  -> data/chunks.jsonl
python embed.py      # 2. embed chunks into ChromaDB         -> chroma_db/
python app.py        # 3. launch the Gradio UI at http://localhost:7860
```

You need a free `GROQ_API_KEY` in `.env` (copy `.env.example`). Retrieval can be tested
without a key via `python retrieve.py`; full Q&A and `python evaluate.py` require it.

**Pipeline:** Ingestion (`pdfplumber`) → Chunking (recursive, ~800/150) → Embedding +
Vector Store (`all-MiniLM-L6-v2` + ChromaDB) → Retrieval (top-k=4 cosine) → Generation
(Groq `llama-3.3-70b-versatile`, grounded + cited). See `planning.md` for the spec and
architecture diagram.

---

## Domain

This system covers **how to become a Flight Instructor with a Sport Pilot rating (CFI-S)**,
and the knowledge such an instructor must hold and teach.

This knowledge is valuable but genuinely hard to find in one place. The official answers
exist, but they are scattered across federal regulations (14 CFR), separate FAA testing
standards (ACS/PTS), advisory circulars, and multi-hundred-page handbooks — each written in
dense, cross-referencing "FAA-ese." Answering a single practical question often requires
knowing *which* document holds the answer: aeronautical-experience requirements live in 14
CFR Part 61, checkride tasks live in the ACS/PTS, teaching theory lives in the Aviation
Instructor's Handbook, and endorsement wording lives in an Advisory Circular. This system
makes that corpus searchable in plain language.

---

## Document Sources

10 public-domain FAA / U.S. Government publications (1,099 pages), downloaded from faa.gov
and govinfo.gov. Full provenance in [`documents/SOURCES.md`](documents/SOURCES.md).

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | 14 CFR Part 1 — Definitions | Regulation | https://www.govinfo.gov/content/pkg/CFR-2024-title14-vol1/pdf/CFR-2024-title14-vol1-part1.pdf |
| 2 | 14 CFR Part 61 — Certification: Pilots & Flight Instructors | Regulation | https://www.govinfo.gov/content/pkg/CFR-2024-title14-vol2/pdf/CFR-2024-title14-vol2-part61.pdf |
| 3 | 14 CFR Part 91 — General Operating & Flight Rules | Regulation | https://www.govinfo.gov/content/pkg/CFR-2024-title14-vol2/pdf/CFR-2024-title14-vol2-part91.pdf |
| 4 | AC 61-65K — Certification: Pilots & Flight/Ground Instructors | Advisory Circular | https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_61-65K.pdf |
| 5 | FAA-G-ACS-2 — ACS Companion Guide for Pilots | Guidance | https://www.faa.gov/training_testing/testing/acs/acs_companion_guide_pilots.pdf |
| 6 | FAA-H-8083-2A — Risk Management Handbook | Handbook | https://www.faa.gov/sites/faa.gov/files/2022-06/risk_management_handbook_2A.pdf |
| 7 | FAA-H-8083-9A — Aviation Instructor's Handbook | Handbook | https://www.govinfo.gov/content/pkg/GOVPUB-TD4-PURL-LPS109875/pdf/GOVPUB-TD4-PURL-LPS109875.pdf |
| 8 | FAA-S-8081-29 — Sport Pilot & Sport Pilot Flight Instructor PTS | Testing standard | https://www.faa.gov/sites/faa.gov/files/training_testing/testing/test_standards/faa-s-8081-29.pdf |
| 9 | FAA-S-ACS-25 — Flight Instructor (Airplane) ACS | Testing standard | https://www.faa.gov/training_testing/testing/acs/cfi_airplane_acs_25.pdf |
| 10 | FAA-S-ACS-6C — Private Pilot (Airplane) ACS | Testing standard | https://www.faa.gov/training_testing/testing/acs/private_airplane_acs_6.pdf |

The set is deliberately varied (regulations, testing standards, advisory guidance,
handbooks) because different question types resolve to different document types.

---

## Chunking Strategy

**Chunk size:** ~800 characters (≈160 tokens)

**Overlap:** 150 characters (~19%)

**Why these choices fit your documents:** The corpus mixes dense regulatory text with
numbered subsections (Parts 1/61/91), structured ACS/PTS task tables, and flowing handbook
prose. I use a **recursive split** that prefers natural boundaries (paragraph → sentence →
word), so chunks tend to end at a real boundary instead of mid-sentence — important for
regulations, where a lettered subsection is a self-contained unit. The ~800-char target is
driven by the embedding model: **all-MiniLM-L6-v2 truncates input at 256 tokens (~1,000
chars)**, so sizing chunks at ~160 tokens keeps the whole chunk *plus* overlap inside that
window with nothing silently cut off. The 150-char overlap guards against a fact landing on
a chunk boundary (e.g., a requirement whose condition and exception fall in adjacent chunks).

**Preprocessing before chunking** (see `ingest.py`): the CFR regulations and handbooks are
printed in **two columns**, which a naive `pdfplumber.extract_text()` interleaves into
nonsense. I detect the column layout per page (by finding the vertical gutter the fewest
words cross) and read each column separately. I also strip boilerplate: GovInfo `VerDate`
machine footers, CFR running headers, ACS/PTS page footers (via regex), repeated
running-header/footer lines (via frequency analysis), and rotated watermark text (by keeping
only upright words).

**Final chunk count:** **5,629 chunks** (avg 711 chars, range 94–950). This exceeds the
project's 50–2,000 guideline; see the [Spec Reflection](#spec-reflection) for why keeping
~800-char chunks is the correct call here.

### Sample chunks (with source)

1. **`14-CFR-Part-61` (chunk 802):** "…§61.183 Eligibility requirements. To be eligible for a flight instructor certificate or rating a person must: (a) Be at least 18 years of age; (b) Be able to read, speak, write, and understand the English language."
2. **`FAA-H-8083-9A` Aviation Instructor's Handbook (chunk 188):** "These laws are universally accepted and apply to all kinds of learning: the law of readiness, the law of exercise, and the law of effect. Since Thorndike set down his laws, three more have been added: the law of primacy, the law of intensity, and the law of recency…"
3. **`FAA-S-ACS-25` Flight Instructor ACS (chunk 307):** "…AI.XI.D.K1 Flight instruments as they relate to: a. Instrument limitations and potential errors … d. Proper instrument cross-check techniques. Management: The applicant explains and teaches how to identify and manage risk associated with…"
4. **`FAA-H-8083-2A` Risk Management Handbook (chunk 174):** "…The risk mitigation process may start days or weeks before a flight and depends on the complexity of the plan. Air carrier, charter, and fractional operations conducted under 14 CFR parts 121, 135, and 91 Subpart K normally preclude operations in the serious and high-risk categories…"
5. **`FAA-S-8081-29` Sport Pilot Flight Instructor PTS (chunk 343):** "…instructor seeking privileges to provide flight training in an additional category/class of light-sport aircraft is required by 14 CFR part 61 to: 1. hold a valid pilot certificate with ratings appropriate to the flight instructor category and class … 3. successfully pass a proficiency check…"

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (384-dim, runs locally, no
API key or rate limits). Embeddings are normalized and stored in ChromaDB configured for
**cosine** distance. Retrieval uses **top-k = 4**.

**Production tradeoff reflection:** If I deployed this for real users and cost weren't the
constraint, I'd weigh:
- **Context length / accuracy:** a model with a longer input window (e.g., `bge-base`, or an
  API model like OpenAI `text-embedding-3-large`) would let me use larger chunks without
  MiniLM's 256-token truncation and generally retrieve more accurately on dense regulatory
  text — directly relevant to the Q4 failure below, where the key regulation didn't rank.
- **Domain fit:** FAA text is jargon-heavy ("endorsement," "aeronautical experience"). I'd
  A/B test a stronger or technical/legal-tuned model on my question set before paying for it.
- **Latency & operability:** a local model has predictable latency, no per-call cost, and no
  vendor dependency; an API model adds network latency and cost but offloads compute.
- **Multilingual:** not a priority for an English-only FAA corpus, so I wouldn't pay for it.

---

## Retrieval Test Results

Three evaluation queries, with the top retrieved chunks (source + cosine distance). All top
results are below the 0.5 relevance target. (Reproduce with `python retrieve.py`.)

**Query A — "What are the eligibility requirements to apply for a flight instructor certificate?"**
- `14-CFR-Part-61` chunk 802 — **0.197** — §61.183 "Eligibility requirements" text
- `AC_61-65K` chunk 108 — 0.232 — commercial/ATP + instrument requirement
- `AC_61-65K` chunk 115 — 0.240 — sport-pilot CFI eligibility (§61.405)
- `14-CFR-Part-61` chunk 805 — 0.243 — instructor ratings + fundamentals-of-instructing endorsement

*Why these are relevant:* the top hit is the exact regulation defining eligibility (§61.183);
the supporting chunks add the certificate/rating prerequisites and the sport-pilot-specific
path. Together they cover the question from both the regulation and the advisory circular.

**Query B — "What are the laws of learning and what does the law of primacy mean?"**
- `FAA-H-8083-9A` chunk 0 — 0.364 — handbook cover/preface (noise)
- `FAA-H-8083-9A` chunk 188 — 0.379 — lists all six laws of learning
- `FAA-H-8083-9A` chunk 187 — 0.380 — adjacent learning-theory prose

*Why these are relevant:* despite a noisy top hit (the cover page, which shares vocabulary
like "instructor/learning"), chunk 188 contains exactly the six named laws, which is enough
for a correct grounded answer.

**Query C — "What must an instructor do before endorsing a student for their first solo flight?"**
- `FAA-H-8083-9A` chunks 924 / 1037 / 110 / 1046 — 0.322–0.343 — instructor *responsibility* for solo

This query is **partially off-target**: it retrieves the handbook's discussion of instructor
responsibility for solo supervision rather than **§61.87**, which actually enumerates the
pre-solo requirements. This drives the documented failure case below.

---

## Grounded Generation

**System prompt grounding instruction** (see `query.py`): the model is told to answer using
*only* the retrieved excerpts, with explicit rules:

> "Use only information contained in the excerpts. Do not use any outside or prior knowledge,
> even if you think you know the answer. If the excerpts do not contain enough information to
> answer, reply with exactly: 'I don't have enough information on that.' … Do not fabricate
> regulation numbers, requirements, or sources."

The retrieved chunks are formatted as a numbered, source-labeled context block and passed in
the user message; generation runs at `temperature=0.0` for deterministic, factual output.

**How source attribution is surfaced:** citations are attached **programmatically**, not left
to the LLM. After generation, `ask()` collects the unique source filenames from the retrieved
chunks' metadata and returns them alongside the answer, so every answer shows its sources
regardless of what the model writes. On a refusal, sources are suppressed (no source supports
a non-answer).

---

## Example Responses

**1. Grounded answer with source attribution** — *"How old must a flight instructor be, and what are the eligibility requirements?"*
> To be eligible for a flight instructor certificate, a person must be at least 18 years of
> age (§61.183(a)) and able to read, speak, write, and understand English (§61.183(b)).
> Additional requirements include holding a commercial or ATP certificate with an appropriate
> category/class rating and an instrument rating, plus the required logbook endorsements.
>
> **Sources:** 14-CFR-Part-61_Certification-Pilots-Flight-Instructors.pdf, AC_61-65K_Certification-Pilots-Flight-Ground-Instructors.pdf

**2. Grounded answer with source attribution** — *"What are the laws of learning and what does primacy mean?"*
> The laws of learning are: readiness, exercise, effect, primacy, intensity, and recency. The
> law of primacy means it is important for the instructor to make sure the student gets it
> right the first time, because what is learned first creates a strong impression.
>
> **Sources:** FAA-H-8083-9A_Aviation-Instructors-Handbook.pdf

**3. Out-of-scope query (refusal)** — *"What is the boiling point of water on the surface of Mars?"*
> I don't have enough information on that.
>
> **Sources:** (none)

---

## Query Interface

A Gradio web UI (`python app.py`, http://localhost:7860).

- **Input field:** "Your question" — a free-text box for a natural-language question (also
  submittable with Enter). Example questions are provided as one-click buttons.
- **Output fields:** "Answer" — the grounded response; "Retrieved from" — the bullet list of
  FAA source document(s) the answer drew from.

**Sample interaction transcript:**
```
Your question:  Can a sport pilot become a flight instructor, and what must they hold?
Answer:         A sport pilot can become a flight instructor. To be eligible for a flight
                instructor certificate with a sport pilot rating, an applicant must:
                1. Hold at least a sport pilot certificate with category and class ratings
                   or privileges (14 CFR §61.403),
                2. Have a logbook endorsement certifying the aeronautical experience
                   required by 14 CFR §61.411, and
                3. Have a logbook endorsement certifying ground and flight training
                   required by 14 CFR §61.409 and competency to pass the practical
                   test (14 CFR §61.405).
Retrieved from: • FAA-S-8081-29_Sport-Pilot-and-Sport-Pilot-Flight-Instructor-PTS.pdf
                • AC_61-65K_Certification-Pilots-Flight-Ground-Instructors.pdf
```

---

## Evaluation Report

Full machine-generated report (with retrieved chunks per question) in
[`eval_results.md`](eval_results.md). Summary:

| # | Question | Expected answer | System response (summarized) | Retrieval | Accuracy |
|---|----------|-----------------|------------------------------|-----------|----------|
| 1 | Eligibility to apply for a flight instructor certificate? | §61.183: ≥18, English, commercial/ATP + instrument, tests, endorsements | Stated age/English with §61.183 cites; added commercial/ATP + instrument + sport-pilot path | Relevant (0.197) | **Accurate** |
| 2 | Privileges & limits of a sport pilot flight instructor? | Subpart K: trains toward sport pilot in authorized cat/class, needs endorsements, limited to LSA | Hedged; gave related "adding privileges" info but not the core privilege/limit statement | Partially relevant (0.268) | **Partially accurate** |
| 3 | Laws of learning + meaning of primacy? | Six laws; primacy = first impression sticks | Listed all six laws correctly; explained primacy | Relevant (0.364) | **Accurate** |
| 4 | What must an instructor do before first solo endorsement? | §61.87: presolo written test, logged training in make/model, logbook endorsements | Only "demonstrate consistent ability to perform fundamental maneuvers" — missed §61.87 specifics | **Off-target (0.322)** | **Inaccurate** |
| 5 | Can a sport pilot CFI train a student toward a Private Pilot certificate? | No — sport CFI is limited to sport-pilot training | Implied yes via a "permitted credit" subsection — answered the wrong question | Partially relevant (0.320) | **Partially accurate / misleading** |

**Result spread:** 2 accurate, 2 partial, 1 inaccurate.

---

## Failure Case Analysis

**Question that failed:** Q4 — "What must an instructor do before endorsing a student for
their first solo flight?"

**What the system returned:** "Before endorsing a student for their first solo flight, the
instructor should require the student to demonstrate consistent ability to perform all of the
fundamental maneuvers." This omits the actual regulatory requirements (the instructor-
administered **presolo written test**, logged training on required maneuvers in the specific
make/model, and the **logbook endorsements** of §61.87).

**Root cause (tied to a specific pipeline stage):** this is a **retrieval** failure. All four
retrieved chunks came from the Aviation Instructor's Handbook's prose about instructor
*responsibility* for solo supervision; **§61.87** — which enumerates the pre-solo requirements
— never entered the top-4. The query "what must an instructor do before endorsing… solo" is
semantically closest to the handbook's narrative about endorsing solo flight, whereas §61.87
is written as a dense regulatory list ("presolo knowledge test," "maneuvers and procedures")
that shares little surface vocabulary with the question. Semantic similarity matched the
*topic* but not the *regulation*. Generation then faithfully grounded its answer in the
(insufficient) retrieved context — so the grounding worked, but on the wrong chunks.

**What I would change to fix it:** I implemented **hybrid retrieval** (BM25 + semantic, see the
Stretch Feature section below) expecting it to fix this — and it **did not**, which is itself
instructive. The corpus *does* contain the answer (Part 61, chunks 475–476: "(c) Pre-solo flight
training. Prior to conducting a solo flight, a student pilot must…"), but the regulation uses
the term **"pre-solo"** while the natural query says "before… solo," so *neither* the embedding
*nor* the keyword retriever ranks it. The real fix is to bridge that vocabulary gap: **query
expansion** (e.g., expand "before first solo" → "pre-solo requirements §61.87"), or
**section-aware retrieval** that indexes the regulation's section headings. Probe queries that
use the regulation's own vocabulary ("pre-solo knowledge test and flight training") *do* surface
chunks 475–476, confirming the content is reachable — the failure is query–document term
mismatch, not missing data. (Q5 was a related gap that hybrid *did* fix; see below.)

---

## Stretch Feature: Hybrid Search (semantic + BM25)

**What I built:** a second retrieval mode that combines the embedding (cosine) search with a
**BM25** keyword index over the same 5,629 chunks, fused with **Reciprocal Rank Fusion (RRF)**
(`score = Σ 1/(60 + rank)` across the two ranked lists; rank-based, so no score normalization
needed). It's a `mode="hybrid"` argument on `retrieve()` / `ask()`, so semantic-only stays
available for comparison. (Reproduce: `python evaluate_hybrid.py` → `eval_hybrid_comparison.md`.)

**Result — semantic vs. hybrid on the 5 eval questions:**

| # | Question | Semantic | Hybrid | What hybrid changed |
|---|----------|----------|--------|---------------------|
| 1 | Flight instructor eligibility | Accurate | Accurate | Neutral — also pulled the sport-pilot path (§61.403) |
| 2 | Sport CFI privileges & limits | Partially accurate | **Accurate** | BM25 matched "privileges"/"limits"/"sport pilot instructor" and surfaced **§61.413 (privileges) and §61.415 (limits)**, which semantic missed |
| 3 | Laws of learning / primacy | Accurate | Accurate | Neutral — both correct (hybrid's primacy definition slightly fuller) |
| 4 | Pre-solo endorsement | Inaccurate | **Inaccurate (not fixed)** | No change — §61.87 still not retrieved (vocabulary mismatch; see Failure Case) |
| 5 | Sport CFI → Private training? | Partial / misleading | **Accurate** | Surfaced **§61.415** and correctly concluded a sport CFI cannot conduct private-pilot training |

**Net: accuracy improved from 2/5 → 4/5, with zero regressions.** Hybrid's gains (Q2, Q5) both
came from BM25 surfacing the *specific regulation section* whose keywords matched the query, where
semantic search had returned topically-related-but-imprecise chunks.

**Honest limitation:** hybrid did **not** fix the documented primary failure (Q4). The win
condition for keyword search is shared surface terms, and the natural Q4 query ("before… first
solo") shares none with §61.87's "pre-solo" text — so BM25 ranked the same handbook chunks as the
embeddings. Probe queries using the regulation's own vocabulary do retrieve the right chunks, which
locates the remaining problem as **query–document term mismatch** (addressable with query expansion
or section-aware indexing), not a retrieval-algorithm choice. The takeaway: hybrid search reliably
helps when the user's wording overlaps the source's wording, but it is not a cure for semantic
vocabulary gaps.

---

## Spec Reflection

**One way the spec helped you during implementation:** Pinning the chunk size to the embedding
model's token window in `planning.md` *before* writing code prevented a real bug. The spec's
Chunking Strategy section explicitly noted all-MiniLM-L6-v2's 256-token truncation limit, so I
sized chunks at ~800 chars from the start rather than discovering mid-project that larger
chunks were being silently cut off. The architecture diagram also made it obvious which tool
owned each stage, so each script (`ingest` → `embed` → `retrieve` → `query`) had a single,
clear responsibility.

**One way your implementation diverged from the spec, and why:** The spec planned to keep the
chunk count within the 50–2,000 guideline and, if it ran high, to raise chunk size toward
~1,000 chars. On implementation this didn't work: the corpus is 1,099 pages, so ~800-char
chunks produced **5,629 chunks**, and ~1,000-char chunks would still yield ~4,600 — while the
only way to reach 2,000 chunks (~2,200-char chunks) would blow past MiniLM's 256-token window
and truncate text. I therefore **kept ~800-char chunks and accepted the higher count.** The
50–2,000 guideline targets smaller/noisier corpora where a high count signals thin, low-signal
fragments; my chunks average 711 chars and are self-contained, and 5,629 vectors is trivial
for ChromaDB. The real binding constraint is the embedding window, not the chunk count.

---

## AI Usage

> *(Drafted from how this project was actually built with Claude Code — edit to match your own
> experience and voice before submitting.)*

**Instance 1 — Ingestion + chunking (`ingest.py`)**
- *What I gave the AI:* my `planning.md` Documents and Chunking Strategy sections, plus the
  observation that the CFR PDFs and handbooks are two-column.
- *What it produced:* a pipeline that loaded the PDFs, extracted text, cleaned boilerplate,
  and chunked at ~800/150. The first version used a naive `extract_text()` that scrambled the
  two-column layouts (left and right columns interleaved line-by-line).
- *What I changed or overrode:* I directed it to add per-page **column detection** and extract
  each column separately, and to verify by printing sample chunks. The first column-detection
  heuristic mis-flagged two-column CFR pages as single-column; I had it switch from a wide
  "gutter band" test to counting words that actually **cross the centerline**, which fixed it.

**Instance 2 — Grounded generation (`query.py`)**
- *What I gave the AI:* my grounding requirement (answer only from retrieved context; refuse
  otherwise) and the decision to attach citations programmatically.
- *What it produced:* a `query.py` with a grounding system prompt and a `format_response`
  helper that listed sources after every answer.
- *What I changed or overrode:* in live testing, the out-of-scope ("Mars") refusal still
  printed a Sources list, which is misleading. I directed a change to **suppress sources on
  refusal**, so a non-answer never shows false attribution.
