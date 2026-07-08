"""Flatten a SEC company-facts blob into a searchable list of USD values."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FactRef:
    concept: str
    period_end: str
    value: float
    unit: str


def build_value_index(company_facts: dict) -> list[FactRef]:
    """Extract every numeric fact from a company-facts blob.

    Keeps the concept/period/unit so a matched figure can be cited back to the
    exact XBRL datapoint that supports it.
    """
    refs: list[FactRef] = []
    for _taxonomy, concepts in company_facts.get("facts", {}).items():
        for concept, body in concepts.items():
            for unit, entries in body.get("units", {}).items():
                for e in entries:
                    val = e.get("val")
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        refs.append(
                            FactRef(concept, e.get("end", ""), float(val), unit)
                        )
    return refs
