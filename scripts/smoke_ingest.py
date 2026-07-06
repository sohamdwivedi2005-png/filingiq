"""Smoke test: prove end-to-end SEC ingestion works.

Resolves tickers -> CIK, pulls the latest 10-K metadata, and extracts
ground-truth annual revenue from XBRL structured data. Run with:

    uv run python scripts/smoke_ingest.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from filingiq.ingest.sec_client import REVENUE_TAGS, SecClient  # noqa: E402

TICKERS = ["AAPL", "MSFT", "NVDA"]


def main() -> None:
    with SecClient() as sec:
        for ticker in TICKERS:
            cik = sec.cik_for_ticker(ticker)
            print(f"\n{'=' * 66}\n{ticker}  (CIK {cik})\n{'=' * 66}")

            latest = sec.latest_filing(cik, form="10-K")
            print(f"Latest 10-K: filed {latest.filing_date} "
                  f"(period end {latest.report_date})")
            print(f"  accession {latest.accession}")
            print(f"  {latest.url}")

            print("Ground-truth annual revenue (from XBRL):")
            for f in sec.annual_facts_multi(cik, REVENUE_TAGS)[-6:]:
                print(f"  FY{f.fy} {f.fp} | end {f.period_end} | "
                      f"${f.value:,.0f}  [{f.concept}]")


if __name__ == "__main__":
    main()
