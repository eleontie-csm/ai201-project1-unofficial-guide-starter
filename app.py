"""
Milestone 5b — Query interface (Gradio web UI).

A minimal but demo-ready interface: type a question, get a grounded answer plus the
FAA source document(s) it was drawn from. Wraps the end-to-end ask() from query.py.

Run:  python app.py     then open http://localhost:7860
"""

import gradio as gr

from query import ask

EXAMPLES = [
    "What are the eligibility requirements to apply for a flight instructor certificate?",
    "What are the laws of learning and what does the law of primacy mean?",
    "What must an instructor do before endorsing a student for their first solo flight?",
    "Can a sport pilot flight instructor train a student toward a Private Pilot certificate?",
]


def handle_query(question):
    if not question or not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"]) or "(no sources cited)"
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide — Sport Flight Instructor") as demo:
    gr.Markdown(
        "# The Unofficial Guide: Becoming a Sport Flight Instructor\n"
        "Ask a plain-language question. Answers are grounded in official FAA documents "
        "(regulations, ACS/PTS, advisory circulars, and handbooks) and cite their sources."
    )
    inp = gr.Textbox(label="Your question", placeholder="e.g. How old must a flight instructor be?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])
    gr.Examples(EXAMPLES, inputs=inp)


if __name__ == "__main__":
    demo.launch()
