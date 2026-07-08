"""Run FilingIQ's eval suites and gate on thresholds (exit 1 on regression).

    uv run python scripts/run_evals.py                  # both suites
    uv run python scripts/run_evals.py --retrieval-only # no LLM / API key needed
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from filingiq.evals import core  # noqa: E402

# CI gate thresholds — a change that drops below these fails the build.
MIN_HIT_AT_K = 0.70
MIN_NUMERIC_ACCURACY = 0.70


def retrieval_suite(k: int) -> bool:
    results = core.run_retrieval(core.load("retrieval.json"), k=k)
    m = core.retrieval_metrics(results)
    print(f"\n=== RETRIEVAL (n={m['n']}, k={k}) ===")
    for r in results:
        mark = f"rank {r.rank}" if r.rank else "MISS"
        print(f"  [{'ok' if r.rank else '!!'}] {r.ticker} want Item {r.expected_item:<3} "
              f"({mark})  {r.query[:52]}")
    print(f"  hit@{k}={m['hit_at_k']:.0%}  MRR={m['mrr']:.3f}  "
          f"(gate hit@{k} >= {MIN_HIT_AT_K:.0%})")
    return m["hit_at_k"] >= MIN_HIT_AT_K


def numeric_suite() -> bool:
    results = core.run_numeric(core.load("numeric.json"))
    m = core.numeric_metrics(results)
    print(f"\n=== NUMERIC vs XBRL (n={m['n']}) ===")
    for r in results:
        gt = f"{r.expected:,.0f}" if r.expected is not None else "no ground truth"
        print(f"  [{'ok' if r.stated_correct else '!!'}] {r.ticker} FY{r.fiscal_year}: "
              f"stated={'Y' if r.stated_correct else 'N'} "
              f"verified={'Y' if r.verified else 'N'}  (truth {gt})")
    print(f"  accuracy={m['accuracy']:.0%}  verified_rate={m['verified_rate']:.0%}  "
          f"(gate accuracy >= {MIN_NUMERIC_ACCURACY:.0%})")
    return m["accuracy"] >= MIN_NUMERIC_ACCURACY


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--retrieval-only", action="store_true")
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args()

    passed = retrieval_suite(args.k)
    if not args.retrieval_only:
        passed = numeric_suite() and passed

    print(f"\n{'PASS' if passed else 'FAIL'} — eval gate")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
