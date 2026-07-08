"""Reconcile extracted dollar figures against the XBRL ground-truth values."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from filingiq.verify.extract import extract_amounts
from filingiq.verify.facts import FactRef

# Tight relative tolerance so a figure matches the RIGHT datapoint, not a
# coincidentally-close one. A large company has thousands of XBRL values, so a
# loose band produces false provenance. 0.5% still admits round-to-billion quotes
# ("$391 billion" vs 391.035e9 = 0.009% off) while rejecting near-misses.
_REL_TOL = 0.005


@dataclass(frozen=True)
class Verdict:
    raw: str
    value: float
    status: str  # "verified" | "unverified"
    concept: str | None
    period_end: str | None


def _rel_err(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1.0)


def verify_text(text: str, refs: Sequence[FactRef]) -> list[Verdict]:
    """Flag each dollar figure in `text` as verified against XBRL, or not.

    A figure is verified against the *closest* XBRL value within tolerance (so the
    cited concept/period is the right one). Figures without a scale word (e.g.
    "$93,736") are also tested ×1e6, since filing tables are often in millions.
    """
    usd = [r for r in refs if r.unit == "USD"]
    verdicts: list[Verdict] = []
    seen: set[float] = set()
    for claim in extract_amounts(text):
        key = round(claim.value, 2)
        if key in seen:  # the model often repeats the same figure
            continue
        seen.add(key)
        candidates = [claim.value] if claim.scaled else [claim.value, claim.value * 1e6]
        best: FactRef | None = None
        best_err = _REL_TOL
        for cand in candidates:
            for ref in usd:
                err = _rel_err(cand, ref.value)
                if err <= best_err:
                    best_err = err
                    best = ref
        verdicts.append(
            Verdict(
                raw=claim.raw,
                value=claim.value,
                status="verified" if best else "unverified",
                concept=best.concept if best else None,
                period_end=best.period_end if best else None,
            )
        )
    return verdicts
