"""Ollama chat client (OpenAI-compatible local endpoint).

Used to serve the fine-tuned FilingIQ model locally so it can be plugged behind
the same adapter and scored by the same eval harness as Groq:

    LLM_PROVIDER=ollama LLM_MODEL=filingiq-qwen3b uv run python scripts/run_evals.py
"""

from __future__ import annotations

import httpx

from filingiq import config
from filingiq.llm.base import Message


class OllamaLLM:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        timeout: float = 120.0,  # local inference can be slow
    ) -> None:
        self.model = model or config.LLM_MODEL
        self._base = (base_url or config.OLLAMA_BASE_URL).rstrip("/")
        self._temperature = config.LLM_TEMPERATURE if temperature is None else temperature
        self._client = httpx.Client(timeout=timeout)

    def complete(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        payload: dict = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": self._temperature if temperature is None else temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        resp = self._client.post(f"{self._base}/chat/completions", json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> OllamaLLM:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
