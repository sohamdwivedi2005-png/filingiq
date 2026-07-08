# FilingIQ

Auditable, multi-agent Q&A over SEC filings — grounded in the SEC's own **XBRL
structured data** so every figure is verifiable, not guessed.

This is a portfolio project demonstrating production AI engineering: retrieval,
multi-agent orchestration, a numeric-verification loop, and — the centerpiece —
an **offline eval harness with a CI gate** that measures accuracy against ground
truth. The point is not to out-answer a chatbot on easy questions; it is to make
an AI system's output **auditable, reproducible, and measurable** enough to run
in production.

## Status

- [x] **Phase 0 / ingestion**: SEC EDGAR client (ticker → CIK, filing metadata,
      XBRL annual facts). See `scripts/smoke_ingest.py`.
- [ ] Filing document parsing + section-aware chunking
- [ ] Hybrid retrieval + reranking (LanceDB)
- [ ] Numeric-verification loop + numeric-extraction eval vs. XBRL
- [ ] Multi-agent orchestrator + cited ReportAgent
- [ ] Eval harness (numeric / retrieval / faithfulness) + CI gate

## Stack (tuned for a local, free-forever, laptop-class build)

- **Python 3.12** managed by [`uv`](https://docs.astral.sh/uv/) (3.14 lacks ML wheels).
- **Data**: SEC EDGAR free APIs (no key; requires a `User-Agent`).
- **Vector store**: LanceDB (embedded — no Docker/Postgres server needed).
- **LLM**: behind a swappable provider adapter — small local model (Ollama) or a
  free API. Added when the Q&A phase needs it; ingestion/retrieval do not.
- The "production" path (pgvector + self-hosted Langfuse via Docker) stays
  documented and swappable, but is not required for local development.

## Setup

```bash
uv sync                                   # creates .venv (Python 3.12) + deps
cp .env.example .env                      # set your SEC User-Agent contact
uv run python scripts/smoke_ingest.py     # prove ingestion works
```

## Layout

```
src/filingiq/
  config.py            # env-driven settings (SEC User-Agent, rate limit)
  ingest/
    sec_client.py      # SEC EDGAR API client
scripts/
  smoke_ingest.py      # end-to-end ingestion smoke test
```

## RAG retrieval (working)

`build_index.py` → fetch latest 10-K, split narrative items into citable chunks
(`rag/chunk.py`), embed with bge-small via fastembed (CPU/ONNX, no torch), store
in LanceDB. Item 8 (financials) is excluded — those numbers come from XBRL ground
truth, not fuzzy text search.

`search_index.py` supports three modes, all returning `ticker · filing · item ·
chunk` citations:
- **dense** — vector similarity only
- **hybrid** (default) — dense + BM25 fused by Reciprocal Rank Fusion
- **hybrid + `--cross`** — cross-encoder reranks the fused candidates
  (fastembed ONNX, no torch) for the sharpest ranking

## Next up

- **Answer synthesis** via the provider adapter (free cloud LLM by default,
  local Ollama optional), grounded with citations + numeric-verification vs XBRL.
- **Eval harness**: numeric-extraction accuracy vs XBRL, retrieval recall@k.

Resolved: XBRL **tag drift** — `annual_facts_multi` merges across candidate
revenue concepts (e.g. NVIDIA's switch from the ASC-606 tag to `Revenues`), each
value recording its source concept for an audit trail.
