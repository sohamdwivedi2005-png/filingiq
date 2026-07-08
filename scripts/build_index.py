"""Fetch tickers' latest 10-Ks, chunk their narrative sections, and index them.

    uv run python scripts/build_index.py             # AAPL
    uv run python scripts/build_index.py AAPL MSFT
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from filingiq.ingest.documents import extract_items, html_to_text  # noqa: E402
from filingiq.ingest.sec_client import SecClient  # noqa: E402
from filingiq.rag.chunk import chunk_sections  # noqa: E402
from filingiq.rag.index import DEFAULT_LANCE, index_chunks  # noqa: E402


def main() -> None:
    tickers = sys.argv[1:] or ["AAPL"]
    all_chunks = []
    with SecClient() as sec:
        for ticker in tickers:
            cik = sec.cik_for_ticker(ticker)
            filing = sec.latest_filing(cik, "10-K")
            sections = extract_items(html_to_text(sec.fetch_text(filing.url)))
            chunks = chunk_sections(
                sections,
                ticker=ticker,
                cik=cik,
                accession=filing.accession,
                report_date=filing.report_date,
            )
            all_chunks.extend(chunks)
            print(f"  {ticker}: {len(chunks)} chunks from {len(sections)} sections")

    print("Embedding + indexing (first run downloads the embed model)...")
    n = index_chunks(all_chunks, reset=True)
    print(f"Indexed {n} chunks -> {DEFAULT_LANCE}")


if __name__ == "__main__":
    main()
