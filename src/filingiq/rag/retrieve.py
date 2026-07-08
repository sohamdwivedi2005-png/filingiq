"""Search the indexed 10-K chunks: dense, or hybrid (dense + BM25) with reranking.

Pipeline for the default hybrid mode:
  1. dense (vector) + sparse (BM25) candidates, fused by Reciprocal Rank Fusion
  2. optionally re-scored by a cross-encoder over just the fused candidates
Each result keeps its citation metadata and a `score` for display.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import lancedb
from lancedb.rerankers import RRFReranker

from filingiq.rag.embed import embed_query
from filingiq.rag.index import DEFAULT_LANCE, TABLE, ensure_fts_index
from filingiq.rag.rerank import cross_rerank

Mode = Literal["dense", "hybrid"]


def _score(row: dict[str, Any]) -> float:
    """Unify the various score fields LanceDB / the reranker attach."""
    if "_rerank_score" in row:
        return row["_rerank_score"]
    if "_relevance_score" in row:
        return row["_relevance_score"]
    if "_distance" in row:
        return -row["_distance"]  # smaller distance = better; flip for a "higher=better"
    return 0.0


def search(
    query: str,
    k: int = 5,
    mode: Mode = "hybrid",
    ticker: str | None = None,
    cross_encoder: bool = False,
    candidates: int = 30,
    db_path: Path | str = DEFAULT_LANCE,
    table: str = TABLE,
) -> list[dict[str, Any]]:
    """Return top-`k` chunks for `query`.

    mode="dense" is vector-only; mode="hybrid" fuses vector + BM25 via RRF.
    Set cross_encoder=True to rerank the fused candidates with a cross-encoder.
    """
    db = lancedb.connect(db_path)
    tbl = db.open_table(table)
    limit = candidates if cross_encoder else k

    def run() -> list[dict[str, Any]]:
        if mode == "dense":
            q = tbl.search(embed_query(query)).limit(limit)
        else:
            q = (
                tbl.search(query_type="hybrid")
                .vector(embed_query(query))
                .text(query)
                .rerank(RRFReranker())
                .limit(limit)
            )
        if ticker:
            q = q.where(f"ticker = '{ticker}'", prefilter=True)
        return q.to_list()

    try:
        rows = run()
    except Exception:  # noqa: BLE001 -- most likely a missing FTS index; build and retry
        ensure_fts_index(tbl)
        rows = run()

    rows = cross_rerank(query, rows, k) if cross_encoder else rows[:k]
    for r in rows:
        r["score"] = _score(r)
    return rows
