"""Grounded answer synthesis: retrieve evidence, then answer only from it.

The prompt forces the model to cite every claim with [n] source markers and to
refuse when the excerpts don't support an answer — no outside knowledge. Numeric
verification against XBRL ground truth is layered on in a later step.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from filingiq.llm import Message, get_llm
from filingiq.llm.base import LLM
from filingiq.rag.retrieve import search

SYSTEM = (
    "You are FilingIQ, a financial analyst that answers questions about SEC "
    "filings STRICTLY from the provided numbered excerpts.\n"
    "Rules:\n"
    "- Use ONLY the excerpts as evidence; do not rely on outside knowledge.\n"
    "- Cite every claim with bracketed source numbers, e.g. [1], [2].\n"
    "- Quote figures exactly as written and cite them.\n"
    "- If the excerpts do not contain the answer, say so plainly — do not guess."
)


@dataclass(frozen=True)
class Answer:
    question: str
    answer: str
    sources: list[dict[str, Any]]


def _format_context(rows: Sequence[dict[str, Any]]) -> str:
    blocks = []
    for i, r in enumerate(rows, 1):
        cite = (
            f"{r['ticker']} 10-K {r['report_date']} "
            f"Item {r['item']} ({r['item_label']}) chunk {r['chunk_index']}"
        )
        blocks.append(f"[{i}] ({cite})\n{r['text']}")
    return "\n\n".join(blocks)


def answer_question(
    question: str,
    k: int = 6,
    ticker: str | None = None,
    cross_encoder: bool = True,
    llm: LLM | None = None,
) -> Answer:
    """Retrieve top-`k` evidence chunks and synthesize a cited answer."""
    rows = search(question, k=k, ticker=ticker, cross_encoder=cross_encoder)
    user = (
        f"Question: {question}\n\n"
        f"Excerpts:\n{_format_context(rows)}\n\n"
        "Answer the question using only these excerpts, with [n] citations:"
    )
    llm = llm or get_llm()
    text = llm.complete([Message("system", SYSTEM), Message("user", user)])
    return Answer(question=question, answer=text, sources=rows)
