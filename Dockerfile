# FilingIQ web app — deployable to Hugging Face Spaces (Docker SDK, port 7860).
FROM python:3.12-slim

# Bake model + index caches into the image so cold start is fast and offline.
ENV PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=7860 \
    HF_HOME=/app/.cache/hf \
    FASTEMBED_CACHE_PATH=/app/.cache/fastembed

WORKDIR /app

# uv for fast, locked installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependencies first (better layer caching).
COPY pyproject.toml uv.lock ./
RUN uv sync --extra rag --frozen --no-dev

# App code.
COPY . .

# Bake the vector index (fetches filings + downloads the embed model at build
# time; no API key needed for indexing). Refresh by rebuilding the image.
RUN uv run python scripts/build_index.py AAPL MSFT NVDA GOOGL AMZN

EXPOSE 7860
CMD ["uv", "run", "python", "scripts/serve.py"]
