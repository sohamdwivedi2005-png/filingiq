"""Ask FilingIQ a question and get a cited, grounded answer.

    uv run python scripts/ask.py "What are Apple's biggest supply chain risks?"
    uv run python scripts/ask.py --ticker AAPL "How did services revenue change?"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from filingiq.llm.groq import MissingAPIKey  # noqa: E402
from filingiq.rag.answer import answer_question  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="+")
    ap.add_argument("--ticker", default=None)
    ap.add_argument("-k", type=int, default=6)
    args = ap.parse_args()

    question = " ".join(args.question)
    print(f"Q: {question}\n")
    try:
        res = answer_question(question, k=args.k, ticker=args.ticker)
    except MissingAPIKey as e:
        print(f"[setup needed] {e}")
        sys.exit(1)

    print(res.answer)
    print("\nSources:")
    for i, s in enumerate(res.sources, 1):
        print(f"  [{i}] {s['ticker']} 10-K {s['report_date']} "
              f"Item {s['item']} ({s['item_label']}) #{s['chunk_index']}")


if __name__ == "__main__":
    main()
