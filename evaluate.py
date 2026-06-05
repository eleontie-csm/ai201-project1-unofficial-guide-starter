"""
Milestone 6 — Evaluation harness.

Runs the 5 evaluation-plan questions from planning.md end-to-end and writes a
markdown report (eval_results.md) capturing, for each question: the expected answer,
the system's actual answer, which chunks were retrieved (source + distance), and a
blank accuracy judgment for the author to fill in (accurate / partial / inaccurate).

Run:  python evaluate.py
"""

from pathlib import Path

from query import ask

OUT = Path("eval_results.md")

# The 5 evaluation questions and their (author-verified) expected answers.
EVAL = [
    {
        "q": "What are the eligibility requirements to apply for a flight instructor certificate?",
        "expected": "Per 14 CFR 61.183: at least 18; able to read/speak/write/understand "
                    "English; hold a commercial or ATP certificate; hold an instrument rating "
                    "(airplane/powered-lift); pass the required knowledge and practical tests; "
                    "receive the required training and endorsements.",
        "judgment": "Accurate",
        "why": "Retrieval pulled §61.183 directly (distance 0.197); the answer states the age "
               "and English requirements with section citations and correctly adds the "
               "commercial/ATP + instrument requirements and the sport-pilot variant from AC 61-65.",
    },
    {
        "q": "What are the privileges and limits of a sport pilot flight instructor's authorization?",
        "expected": "Per 14 CFR Part 61 Subpart K: a sport pilot CFI may give training toward "
                    "sport pilot certificates/privileges within the category/class they are "
                    "authorized for, must hold the appropriate endorsements, and is limited to "
                    "light-sport aircraft.",
        "judgment": "Partially accurate",
        "why": "Retrieval surfaced chunks about *adding* sport-pilot privileges and category/class "
               "endorsements rather than the core privileges/limitations sections. The model "
               "correctly declined to overstate and gave related, true information, but did not "
               "deliver the central privilege-and-limit statement — a retrieval-coverage gap.",
    },
    {
        "q": "What are the laws of learning described in the Aviation Instructor's Handbook, "
             "and what does the law of primacy mean?",
        "expected": "The six laws: readiness, exercise, effect, primacy, intensity, recency. "
                    "Primacy: what is learned first creates a strong, lasting impression, so it "
                    "is important to teach it correctly the first time.",
        "judgment": "Accurate",
        "why": "Despite the noisy top hit (the handbook cover page), chunk 188 carried all six "
               "laws and the answer lists them correctly and explains primacy faithfully.",
    },
    {
        "q": "What must an instructor do before endorsing a student for their first solo flight?",
        "expected": "Per 14 CFR 61.87: the student must pass an instructor-administered presolo "
                    "written test, receive and log training on the required maneuvers in the "
                    "make/model, and the instructor must give the required logbook endorsements "
                    "certifying readiness for solo.",
        "judgment": "Inaccurate (PRIMARY FAILURE CASE)",
        "why": "All four retrieved chunks came from the Aviation Instructor's Handbook's "
               "discussion of instructor *responsibility* for solo supervision; none was §61.87, "
               "which actually enumerates the pre-solo requirements. Cause: this is a RETRIEVAL "
               "failure. The query 'what must an instructor do before endorsing... solo' is "
               "semantically closest to the handbook's prose about endorsing solo flight, while "
               "§61.87's requirements are written as a dense regulatory list ('presolo knowledge "
               "test', 'maneuvers and procedures') that shares little surface vocabulary with the "
               "question. So the regulation never entered the top-4 and the answer omitted the "
               "presolo written test and logbook endorsements. Likely fixes: hybrid keyword+"
               "semantic search (BM25 would catch 'presolo'), or a larger k.",
    },
    {
        "q": "Can a sport pilot flight instructor train a student toward a Private Pilot certificate?",
        "expected": "No — a sport pilot CFI's training authorization is limited to sport pilot "
                    "training; private-pilot training requires a regular flight instructor "
                    "certificate. (Intentionally hard / likely-failure case.)",
        "judgment": "Partially accurate / misleading",
        "why": "The model latched onto a '(l) Permitted credit for flight training received from "
               "a flight instructor with a sport pilot rating' subsection and implied a sport CFI "
               "can train toward a Private certificate. That conflates 'a private applicant may "
               "count some training received from a sport CFI' with 'a sport CFI may conduct "
               "private-pilot training.' The retrieved chunks didn't include a clean statement of "
               "the sport CFI's training limitation, so the grounded answer is technically tied to "
               "the text but answers the wrong question — a subtle, instructive partial failure.",
    },
]


def main():
    lines = ["# Evaluation Report — The Unofficial Guide (Sport Flight Instructor)\n",
             "Generated by `evaluate.py` (run end-to-end against the live system).\n"]

    for i, item in enumerate(EVAL, 1):
        result = ask(item["q"])
        lines.append(f"\n## Q{i}. {item['q']}\n")
        lines.append(f"**Expected answer:** {item['expected']}\n")
        lines.append(f"**System answer:**\n\n> {result['answer'].replace(chr(10), chr(10)+'> ')}\n")
        lines.append("**Retrieved chunks:**\n")
        for j, h in enumerate(result["hits"], 1):
            snippet = " ".join(h["text"].split())[:160]
            lines.append(f"{j}. `{h['source']}` (chunk {h['chunk_index']}, "
                         f"distance {h['distance']:.3f}) — {snippet}...")
        lines.append(f"\n**Sources cited:** {', '.join(result['sources']) or '(none)'}\n")
        lines.append(f"**Accuracy judgment:** {item['judgment']}\n")
        lines.append(f"**Analysis:** {item['why']}\n")
        print(f"Q{i} done — top distance "
              f"{result['hits'][0]['distance']:.3f}, sources: {len(result['sources'])}")

    OUT.write_text("\n".join(lines))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
