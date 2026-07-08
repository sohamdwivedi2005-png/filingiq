"""Query the indexed 10-K chunks and show cited results.

    uv run python scripts/search_index.py "supply chain risks"
    uv run python scripts/search_index.py --mode dense "services revenue"
    uv run python scripts/search_index.py --cross --ticker AAPL "buyback program"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from filingiq.rag.retrieve import search  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="+")
    ap.add_argument("--mode", choices=["dense", "hybrid"], default="hybrid")
    ap.add_argument("--cross", action="store_true", help="cross-encoder rerank")
    ap.add_argument("--ticker", default=None)
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args()

    query = " ".join(args.query)
    label = args.mode + ("+cross" if args.cross else "")
    print(f"Query [{label}]: {query}\n")
    for r in search(query, k=args.k, mode=args.mode, ticker=args.ticker, cross_encoder=args.cross):
        cite = f"{r['ticker']} 10-K {r['report_date']} | Item {r['item']} ({r['item_label']})"
        print(f"[{r['score']:+.3f}] {cite}  #{r['chunk_index']}")
        print("   " + " ".join(r["text"][:220].split()) + " ...\n")


if __name__ == "__main__":
    main()
