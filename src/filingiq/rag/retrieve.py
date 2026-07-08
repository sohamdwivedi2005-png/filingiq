"""Semantic search over the indexed 10-K chunks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import lancedb

from filingiq.rag.embed import embed_query
from filingiq.rag.index import DEFAULT_LANCE, TABLE


def search(
    query: str,
    k: int = 5,
    db_path: Path | str = DEFAULT_LANCE,
    table: str = TABLE,
    ticker: str | None = None,
) -> list[dict[str, Any]]:
    """Return the top-`k` chunks for `query`, optionally filtered to one ticker."""
    db = lancedb.connect(db_path)
    tbl = db.open_table(table)
    q = tbl.search(embed_query(query)).limit(k)
    if ticker:
        q = q.where(f"ticker = '{ticker}'", prefilter=True)
    return q.to_list()
