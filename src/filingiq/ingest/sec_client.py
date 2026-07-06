"""A small, dependency-light client for the free SEC EDGAR data APIs.

Endpoints used (all free, no API key, require a User-Agent):
- company_tickers.json           -> ticker -> CIK mapping
- data.sec.gov/submissions/...   -> filing history (10-K, 10-Q, ...)
- data.sec.gov/api/xbrl/...      -> XBRL structured facts (the ground truth)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx

from filingiq.config import SEC_MIN_INTERVAL_SECONDS, SEC_USER_AGENT

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"
CONCEPT_URL = (
    "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik10}/{taxonomy}/{tag}.json"
)
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc}"


@dataclass(frozen=True)
class Filing:
    form: str
    filing_date: str
    report_date: str
    accession: str
    primary_document: str
    url: str


@dataclass(frozen=True)
class AnnualFact:
    fy: int | None
    fp: str | None
    period_end: str
    value: float
    form: str
    concept: str  # the XBRL tag this value came from (audit trail)


# Companies report top-line revenue under different US-GAAP concepts, and switch
# over time (e.g. NVIDIA moved off the ASC-606 tag). Tried in priority order and
# merged by fiscal period, so a company's full history resolves.
REVENUE_TAGS: tuple[str, ...] = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet",
)


class SecClient:
    """Thin, rate-limited wrapper over the SEC data APIs."""

    def __init__(self, user_agent: str = SEC_USER_AGENT) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"},
            timeout=30.0,
        )
        self._last_request = 0.0

    # -- low level -------------------------------------------------------
    def _get_json(self, url: str) -> Any:
        wait = SEC_MIN_INTERVAL_SECONDS - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        resp = self._client.get(url)
        self._last_request = time.monotonic()
        resp.raise_for_status()
        return resp.json()

    # -- public ----------------------------------------------------------
    def cik_for_ticker(self, ticker: str) -> str:
        """Resolve a ticker to a zero-padded 10-digit CIK string."""
        data = self._get_json(TICKERS_URL)
        target = ticker.upper()
        for row in data.values():
            if row["ticker"].upper() == target:
                return f"{int(row['cik_str']):010d}"
        raise ValueError(f"Ticker not found in SEC index: {ticker}")

    def latest_filing(self, cik10: str, form: str = "10-K") -> Filing:
        """Return metadata for the most recent filing of a given form type."""
        data = self._get_json(SUBMISSIONS_URL.format(cik10=cik10))
        recent = data["filings"]["recent"]
        cik = str(int(cik10))
        for i, f in enumerate(recent["form"]):
            if f == form:
                acc = recent["accessionNumber"][i]
                doc = recent["primaryDocument"][i]
                return Filing(
                    form=f,
                    filing_date=recent["filingDate"][i],
                    report_date=recent["reportDate"][i],
                    accession=acc,
                    primary_document=doc,
                    url=ARCHIVE_URL.format(
                        cik=cik, acc_nodash=acc.replace("-", ""), doc=doc
                    ),
                )
        raise ValueError(f"No {form} filing found for CIK {cik10}")

    def annual_facts(
        self, cik10: str, tag: str, taxonomy: str = "us-gaap"
    ) -> list[AnnualFact]:
        """Return de-duplicated full-year (10-K) values for one XBRL concept.

        These figures are the SEC's own machine-readable numbers and serve as
        the ground truth for FilingIQ's numeric-extraction evals.
        """
        data = self._get_json(
            CONCEPT_URL.format(cik10=cik10, taxonomy=taxonomy, tag=tag)
        )
        seen: set[tuple[str, float]] = set()
        facts: list[AnnualFact] = []
        for u in data["units"].get("USD", []):
            start, end = date.fromisoformat(u["start"]), date.fromisoformat(u["end"])
            days = (end - start).days
            if u.get("form") == "10-K" and 330 <= days <= 400:  # full fiscal year
                key = (u["end"], float(u["val"]))
                if key in seen:
                    continue
                seen.add(key)
                facts.append(
                    AnnualFact(
                        fy=u.get("fy"),
                        fp=u.get("fp"),
                        period_end=u["end"],
                        value=float(u["val"]),
                        form=u["form"],
                        concept=tag,
                    )
                )
        return sorted(facts, key=lambda f: f.period_end)

    def annual_facts_multi(
        self, cik10: str, tags: tuple[str, ...], taxonomy: str = "us-gaap"
    ) -> list[AnnualFact]:
        """Merge full-year values across several candidate XBRL concepts.

        Concepts are tried in priority order; the first tag to report a given
        fiscal period wins. Missing concepts (HTTP 404) are skipped. This is how
        a company that changed revenue tags mid-history resolves fully.
        """
        merged: dict[str, AnnualFact] = {}
        for tag in tags:
            try:
                facts = self.annual_facts(cik10, tag, taxonomy)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    continue  # this company never used this concept
                raise
            for fact in facts:
                merged.setdefault(fact.period_end, fact)
        return sorted(merged.values(), key=lambda f: f.period_end)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SecClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
