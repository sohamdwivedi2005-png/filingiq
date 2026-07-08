"""Pull dollar figures out of free text and normalize them to absolute USD."""

from __future__ import annotations

import re
from dataclasses import dataclass

# $391 billion | $56.2 billion | $110B | $391,035 million | $0.26
_MONEY = re.compile(
    r"\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)\s*(billion|million|thousand|trillion|bn|B|M|K|T)?",
    re.IGNORECASE,
)
_SCALE = {
    "trillion": 1e12, "t": 1e12,
    "billion": 1e9, "bn": 1e9, "b": 1e9,
    "million": 1e6, "m": 1e6,
    "thousand": 1e3, "k": 1e3,
}


@dataclass(frozen=True)
class NumClaim:
    raw: str
    value: float
    scaled: bool  # True if an explicit scale word/suffix (billion/M/...) was present


def extract_amounts(text: str) -> list[NumClaim]:
    claims: list[NumClaim] = []
    for m in _MONEY.finditer(text):
        num = float(m.group(1).replace(",", ""))
        suffix = (m.group(2) or "").lower()
        scale = _SCALE.get(suffix, 1.0)
        claims.append(
            NumClaim(raw=m.group(0).strip(), value=num * scale, scaled=bool(suffix))
        )
    return claims
