"""Batch-ingest a set of tickers into the local SQLite store.

    uv run python scripts/ingest_batch.py                 # default set
    uv run python scripts/ingest_batch.py AAPL TSLA KO    # custom tickers
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from filingiq.ingest.sec_client import REVENUE_TAGS, SecClient  # noqa: E402
from filingiq.store import db  # noqa: E402

DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]


def main() -> None:
    tickers = sys.argv[1:] or DEFAULT_TICKERS
    conn = db.connect()
    with SecClient() as sec:
        for ticker in tickers:
            cik = sec.cik_for_ticker(ticker)
            db.upsert_company(conn, cik, ticker)
            db.upsert_filing(conn, cik, sec.latest_filing(cik, "10-K"))
            facts = sec.annual_facts_multi(cik, REVENUE_TAGS)
            db.upsert_facts(conn, cik, "revenue", facts)
            print(f"  {ticker}: 1 filing, {len(facts)} revenue facts")
    conn.commit()

    counts = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in ("companies", "filings", "facts")
    }
    print(f"\nDB {db.DEFAULT_DB}: "
          f"{counts['companies']} companies, {counts['filings']} filings, "
          f"{counts['facts']} facts")
    conn.close()


if __name__ == "__main__":
    main()
