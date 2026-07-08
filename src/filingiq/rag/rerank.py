"""Optional cross-encoder reranking (fastembed ONNX, CPU, no torch).

A cross-encoder scores each (query, chunk) pair jointly, which is far more
accurate than the bi-encoder similarity used for first-stage retrieval — but too
slow to run over the whole corpus, so we only rerank the fused candidate set.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import Any

# Small, fast, no-torch cross-encoder. bge-reranker-base is more accurate but larger.
CROSS_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"


@lru_cache(maxsize=1)
def _cross():
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    return TextCrossEncoder(model_name=CROSS_MODEL)


def cross_rerank(
    query: str, rows: Sequence[dict[str, Any]], k: int, text_key: str = "text"
) -> list[dict[str, Any]]:
    """Reorder `rows` by cross-encoder relevance to `query`; return top `k`."""
    if not rows:
        return []
    scores = list(_cross().rerank(query, [r[text_key] for r in rows]))
    order = sorted(range(len(rows)), key=lambda i: scores[i], reverse=True)
    out: list[dict[str, Any]] = []
    for i in order[:k]:
        row = dict(rows[i])
        row["_rerank_score"] = float(scores[i])
        out.append(row)
    return out
