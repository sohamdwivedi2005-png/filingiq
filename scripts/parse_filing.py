"""Fetch a company's latest 10-K, clean it to text, and split into item sections.

    uv run python scripts/parse_filing.py            # AAPL
    uv run python scripts/parse_filing.py MSFT
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from filingiq.ingest.documents import extract_items, html_to_text  # noqa: E402
from filingiq.ingest.sec_client import SecClient  # noqa: E402

KEY_ITEMS = {
    "1A": "Risk Factors",
    "7": "MD&A",
    "7A": "Market Risk",
    "8": "Financial Statements",
}


def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    with SecClient() as sec:
        cik = sec.cik_for_ticker(ticker)
        filing = sec.latest_filing(cik, "10-K")
        print(f"{ticker} 10-K (period end {filing.report_date})")
        print(f"  {filing.url}")
        html = sec.fetch_text(filing.url)

    text = html_to_text(html)
    items = extract_items(text)
    print(f"  raw HTML:    {len(html):,} chars")
    print(f"  clean text:  {len(text):,} chars")
    print(f"  sections:    {len(items)} items detected")
    for key, label in KEY_ITEMS.items():
        if key in items:
            preview = items[key][:100].replace("\n", " ")
            print(f"    Item {key:<3} {label:<22} {len(items[key]):>8,} chars | {preview!r}")
        else:
            print(f"    Item {key:<3} {label:<22} (not found)")


if __name__ == "__main__":
    main()
