"""Ask FilingIQ a question and get a cited, XBRL-verified answer.

    uv run python scripts/ask.py --ticker AAPL "How big is the buyback program?"
    uv run python scripts/ask.py "What are Apple's supply chain risks?"   # no verify
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
    ap.add_argument("--ticker", default=None, help="restrict + enable XBRL verify")
    ap.add_argument("--no-verify", action="store_true")
    ap.add_argument("-k", type=int, default=6)
    args = ap.parse_args()

    question = " ".join(args.question)
    verify = bool(args.ticker) and not args.no_verify
    print(f"Q: {question}\n")
    try:
        res = answer_question(question, k=args.k, ticker=args.ticker, verify=verify)
    except MissingAPIKey as e:
        print(f"[setup needed] {e}")
        sys.exit(1)

    print(res.answer)

    if res.verifications:
        print("\nNumeric check (figures vs XBRL ground truth):")
        for v in res.verifications:
            if v.status == "verified":
                print(f"  [OK] {v.raw}  ->  {v.concept} {v.period_end}")
            else:
                print(f"  [??] {v.raw}  ->  not found in XBRL facts")

    print("\nSources:")
    for i, s in enumerate(res.sources, 1):
        print(f"  [{i}] {s['ticker']} 10-K {s['report_date']} "
              f"Item {s['item']} ({s['item_label']}) #{s['chunk_index']}")


if __name__ == "__main__":
    main()
