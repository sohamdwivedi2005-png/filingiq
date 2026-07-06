"""Parse 10-K filing HTML into clean text and coarse item sections.

Section splitting is a heuristic first pass: 10-K item headers ("Item 1A.",
"Item 7.") appear both in the table of contents and at the real section body,
so for each item id we keep the *longest* span — the body, not the TOC entry.
Good enough to feed section-aware chunking; refine later if needed.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

_WS = re.compile(r"[ \t ]+")
_BLANKS = re.compile(r"\n\s*\n+")
_ITEM = re.compile(r"(?im)^\s*Item\s+(\d{1,2}[A-Z]?)\.")


def html_to_text(html: str) -> str:
    """Strip an SEC HTML filing down to readable, whitespace-collapsed text."""
    tree = HTMLParser(html)
    for node in tree.css("script, style"):
        node.decompose()
    root = tree.body or tree.root
    text = root.text(separator="\n") if root else ""
    text = _WS.sub(" ", text)
    text = _BLANKS.sub("\n\n", text)
    return text.strip()


def extract_items(text: str) -> dict[str, str]:
    """Split filing text into {item_id: body}, keeping the longest span per item."""
    matches = list(_ITEM.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        item = m.group(1).upper()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if len(body) > len(sections.get(item, "")):
            sections[item] = body
    return sections
