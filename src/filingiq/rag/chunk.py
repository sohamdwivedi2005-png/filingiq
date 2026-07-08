"""Turn parsed 10-K item sections into retrievable, citable chunks.

Chunks pack whole paragraphs up to a target size (so we don't split mid-thought),
hard-splitting any single oversized paragraph with a little overlap. Each chunk
carries the metadata needed to cite it later: ticker, filing, item, and index.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

# Narrative items worth retrieving over. Item 8 (financial statements) is skipped
# on purpose — those numbers come from XBRL ground truth, not fuzzy text search.
NARRATIVE_ITEMS: frozenset[str] = frozenset(
    {"1", "1A", "1B", "1C", "2", "3", "5", "7", "7A"}
)

ITEM_LABELS: dict[str, str] = {
    "1": "Business",
    "1A": "Risk Factors",
    "1B": "Unresolved Staff Comments",
    "1C": "Cybersecurity",
    "2": "Properties",
    "3": "Legal Proceedings",
    "5": "Market for Registrant's Equity",
    "7": "MD&A",
    "7A": "Quantitative and Qualitative Disclosures About Market Risk",
    "8": "Financial Statements",
}

_PARA = re.compile(r"\n\s*\n")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    ticker: str
    cik: str
    accession: str
    report_date: str
    item: str
    item_label: str
    chunk_index: int
    n_chars: int


def _hard_split(text: str, target: int, overlap: int) -> list[str]:
    step = max(1, target - overlap)
    return [text[i : i + target] for i in range(0, len(text), step)]


def chunk_text(text: str, target: int = 1200, overlap: int = 150) -> list[str]:
    """Greedily pack paragraphs into ~`target`-char chunks; hard-split big ones."""
    paras = [p.strip() for p in _PARA.split(text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(p) > target:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.extend(_hard_split(p, target, overlap))
        elif buf and len(buf) + len(p) + 2 > target:
            chunks.append(buf)
            buf = p
        else:
            buf = f"{buf}\n\n{p}" if buf else p
    if buf:
        chunks.append(buf)
    return chunks


def chunk_sections(
    sections: Mapping[str, str],
    *,
    ticker: str,
    cik: str,
    accession: str,
    report_date: str,
    include_items: frozenset[str] = NARRATIVE_ITEMS,
    target: int = 1200,
    overlap: int = 150,
) -> list[Chunk]:
    """Chunk the selected item sections of one filing into `Chunk`s."""
    out: list[Chunk] = []
    for item, body in sections.items():
        if item not in include_items:
            continue
        label = ITEM_LABELS.get(item, "")
        for i, piece in enumerate(chunk_text(body, target, overlap)):
            out.append(
                Chunk(
                    chunk_id=f"{accession}:item{item}:{i}",
                    text=piece,
                    ticker=ticker,
                    cik=cik,
                    accession=accession,
                    report_date=report_date,
                    item=item,
                    item_label=label,
                    chunk_index=i,
                    n_chars=len(piece),
                )
            )
    return out
