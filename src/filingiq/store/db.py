"""SQLite persistence for companies, filings, and XBRL facts.

Stdlib-only (sqlite3) — no server, no extra dependency. The DB lives under
./data/ (gitignored). Facts are keyed by (cik, metric, period_end) so a value
like FY2024 revenue upserts idempotently while retaining its source concept.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from filingiq.ingest.sec_client import AnnualFact, Filing

DEFAULT_DB = Path("data/filingiq.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    cik    TEXT PRIMARY KEY,
    ticker TEXT,
    name   TEXT
);
CREATE TABLE IF NOT EXISTS filings (
    accession        TEXT PRIMARY KEY,
    cik              TEXT NOT NULL REFERENCES companies(cik),
    form             TEXT,
    filing_date      TEXT,
    report_date      TEXT,
    primary_document TEXT,
    url              TEXT
);
CREATE TABLE IF NOT EXISTS facts (
    cik        TEXT NOT NULL REFERENCES companies(cik),
    metric     TEXT NOT NULL,
    period_end TEXT NOT NULL,
    fy         INTEGER,
    fp         TEXT,
    form       TEXT,
    value      REAL,
    concept    TEXT,
    PRIMARY KEY (cik, metric, period_end)
);
"""


def connect(db_path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    return conn


def upsert_company(
    conn: sqlite3.Connection, cik: str, ticker: str | None = None, name: str | None = None
) -> None:
    conn.execute(
        "INSERT INTO companies(cik, ticker, name) VALUES(?, ?, ?) "
        "ON CONFLICT(cik) DO UPDATE SET "
        "ticker = COALESCE(excluded.ticker, companies.ticker), "
        "name   = COALESCE(excluded.name,   companies.name)",
        (cik, ticker, name),
    )


def upsert_filing(conn: sqlite3.Connection, cik: str, f: Filing) -> None:
    conn.execute(
        "INSERT INTO filings(accession, cik, form, filing_date, report_date, "
        "primary_document, url) VALUES(?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(accession) DO NOTHING",
        (f.accession, cik, f.form, f.filing_date, f.report_date, f.primary_document, f.url),
    )


def upsert_facts(
    conn: sqlite3.Connection, cik: str, metric: str, facts: Iterable[AnnualFact]
) -> None:
    conn.executemany(
        "INSERT INTO facts(cik, metric, period_end, fy, fp, form, value, concept) "
        "VALUES(?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(cik, metric, period_end) DO UPDATE SET "
        "value = excluded.value, concept = excluded.concept, "
        "fy = excluded.fy, fp = excluded.fp, form = excluded.form",
        [(cik, metric, x.period_end, x.fy, x.fp, x.form, x.value, x.concept) for x in facts],
    )
