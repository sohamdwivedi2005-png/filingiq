"""Embed chunks and store them in an on-disk LanceDB table."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import lancedb

from filingiq.rag.chunk import Chunk
from filingiq.rag.embed import embed_passages

DEFAULT_LANCE = Path("data/lancedb")
TABLE = "chunks"


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
        db.open_table(table).add(records)
    else:
        db.create_table(table, data=records)
    return len(records)
