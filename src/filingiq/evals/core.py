"""Metrics for the two eval suites.

- retrieval: does the correct 10-K item appear in the top-k? -> hit@k, MRR
- numeric:   does the answer state the right revenue figure, and does the
             verification loop confirm it? Ground truth is the company's own
             XBRL data, so no manual labeling is required.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from filingiq.ingest.sec_client import REVENUE_TAGS, SecClient
from filingiq.rag.answer import answer_question
from filingiq.rag.retrieve import search
from filingiq.verify.extract import extract_amounts

EVAL_DIR = Path(__file__).resolve().parents[3] / "evals"


def load(name: str) -> list[dict]:
    return json.loads((EVAL_DIR / name).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Retrieval
# --------------------------------------------------------------------------- #
@dataclass
class RetrievalResult:
    query: str
    ticker: str
    expected_item: str
    rank: int | None  # 1-based rank of the first hit, or None if missed


def run_retrieval(cases: list[dict], k: int = 5) -> list[RetrievalResult]:
    results = []
    for c in cases:
        rows = search(c["query"], k=k, ticker=c.get("ticker"))
        rank = next(
            (i for i, r in enumerate(rows, 1) if r["item"] == c["expected_item"]), None
        )
        results.append(
            RetrievalResult(c["query"], c.get("ticker", ""), c["expected_item"], rank)
        )
    return results


def retrieval_metrics(results: list[RetrievalResult]) -> dict:
    n = len(results) or 1
    hits = sum(r.rank is not None for r in results)
    mrr = sum(1.0 / r.rank for r in results if r.rank) / n
    return {"hit_at_k": hits / n, "mrr": mrr, "n": len(results)}


# --------------------------------------------------------------------------- #
# Numeric (ground truth = XBRL)
# --------------------------------------------------------------------------- #
@dataclass
class NumericResult:
    ticker: str
    fiscal_year: int
    expected: float | None
    stated_correct: bool
    verified: bool


def _matches(value: float, target: float, rel: float = 0.01) -> bool:
    # accept the value itself or its x1e6 (table-in-millions) interpretation
    return any(
        abs(v - target) <= rel * abs(target) for v in (value, value * 1e6)
    )


def _answer_states(text: str, target: float) -> bool:
    return any(_matches(c.value, target) for c in extract_amounts(text))


def _revenue_truth(sec: SecClient, ticker: str, fiscal_year: int) -> float | None:
    cik = sec.cik_for_ticker(ticker)
    for f in sec.annual_facts_multi(cik, REVENUE_TAGS):
        if f.fy == fiscal_year:
            return f.value
    return None


def run_numeric(cases: list[dict]) -> list[NumericResult]:
    results = []
    with SecClient() as sec:
        for c in cases:
            truth = _revenue_truth(sec, c["ticker"], c["fiscal_year"])
            if truth is None:
                results.append(
                    NumericResult(c["ticker"], c["fiscal_year"], None, False, False)
                )
                continue
            ans = answer_question(c["question"], ticker=c["ticker"], verify=True)
            stated = _answer_states(ans.answer, truth)
            verified = any(
                v.status == "verified" and _matches(v.value, truth)
                for v in ans.verifications
            )
            results.append(
                NumericResult(c["ticker"], c["fiscal_year"], truth, stated, verified)
            )
    return results


def numeric_metrics(results: list[NumericResult]) -> dict:
    n = len(results) or 1
    return {
        "accuracy": sum(r.stated_correct for r in results) / n,
        "verified_rate": sum(r.verified for r in results) / n,
        "n": len(results),
    }
