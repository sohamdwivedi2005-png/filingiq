"""Embed chunks and store them in an on-disk LanceDB table."""

from __future__ import annotations

import warnings
from collections.abc import Iterable
from pathlib import Path

import lancedb

from filingiq.rag.chunk import Chunk
from filingiq.rag.embed import embed_passages

DEFAULT_LANCE = Path("data/lancedb")
TABLE = "chunks"


def ensure_fts_index(tbl) -> None:
    """(Re)build the full-text (BM25) index on the text column for hybrid search."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # silence the create_fts_index deprecation
        tbl.create_fts_index("text", replace=True)


def index_chunks(
    chunks: Iterable[Chunk],
    db_path: Path | str = DEFAULT_LANCE,
    table: str = TABLE,
    reset: bool = False,
) -> int:
    """Embed `chunks` and write them to LanceDB. Returns the count indexed."""
    chunks = list(chunks)
    if not chunks:
        return 0
    vectors = embed_passages([c.text for c in chunks])
    records = [
        {
            "vector": v,
            "chunk_id": c.chunk_id,
            "text": c.text,
            "ticker": c.ticker,
            "cik": c.cik,
            "accession": c.accession,
            "report_date": c.report_date,
            "item": c.item,
            "item_label": c.item_label,
            "chunk_index": c.chunk_index,
        }
        for c, v in zip(chunks, vectors)
    ]

    Path(db_path).mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(db_path)
    if reset and table in db.table_names():
        db.drop_table(table)
    if table in db.table_names():
        tbl = db.open_table(table)
        tbl.add(records)
    else:
        tbl = db.create_table(table, data=records)
    ensure_fts_index(tbl)  # keep BM25 index in sync for hybrid search
    return len(records)
