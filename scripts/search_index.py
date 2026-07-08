"""Query the indexed 10-K chunks and show cited results.

    uv run python scripts/search_index.py "supply chain risks"
    uv run python scripts/search_index.py "how did services revenue perform"
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from filingiq.rag.retrieve import search  # noqa: E402

DEFAULT_QUERY = "What risks does the company face from supply chain disruptions?"


def main() -> None:
    query = " ".join(sys.argv[1:]) or DEFAULT_QUERY
    print(f"Query: {query}\n")
    for r in search(query, k=5):
        cite = f"{r['ticker']} 10-K {r['report_date']} · Item {r['item']} ({r['item_label']})"
        print(f"[{r['_distance']:.3f}] {cite}  #{r['chunk_index']}")
        print("   " + " ".join(r["text"][:220].split()) + " ...\n")


if __name__ == "__main__":
    main()
