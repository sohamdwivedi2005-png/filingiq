"""CPU/ONNX text embeddings via fastembed (bge-small, 384-dim, no torch).

bge models want an instruction prefix on *queries* but not on passages;
fastembed's `query_embed` / `passage_embed` handle that, with a manual fallback.
The model is lazy-loaded and cached (first call downloads ~130 MB once).
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384
_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _embedder():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=MODEL_NAME)


def embed_passages(texts: Sequence[str]) -> list[list[float]]:
    emb = _embedder()
    fn = getattr(emb, "passage_embed", emb.embed)
    return [v.tolist() for v in fn(list(texts))]


def embed_query(text: str) -> list[float]:
    emb = _embedder()
    fn = getattr(emb, "query_embed", None)
    if fn is not None:
        return next(iter(fn([text]))).tolist()
    return next(iter(emb.embed([_QUERY_PREFIX + text]))).tolist()
