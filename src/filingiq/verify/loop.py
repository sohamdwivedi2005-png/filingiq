"""Fetch (and cache) a company's XBRL facts, then verify an answer's figures."""

from __future__ import annotations

from functools import lru_cache

from filingiq.ingest.sec_client import SecClient
from filingiq.verify.facts import FactRef, build_value_index
from filingiq.verify.verify import Verdict, verify_text


@lru_cache(maxsize=64)
def _facts_for(cik10: str) -> tuple[FactRef, ...]:
    with SecClient() as sec:
        return tuple(build_value_index(sec.company_facts(cik10)))


def verify_answer(text: str, cik10: str) -> list[Verdict]:
    """Verify every dollar figure in `text` against company `cik10`'s XBRL facts."""
    return verify_text(text, _facts_for(cik10))
