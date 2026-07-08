"""Groq chat client (OpenAI-compatible) over httpx — no extra SDK dependency."""

from __future__ import annotations

import httpx

from filingiq import config
from filingiq.llm.base import Message


class MissingAPIKey(RuntimeError):
    pass


class GroqLLM:
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.model = model or config.LLM_MODEL
        self._key = api_key or config.GROQ_API_KEY
        self._base = (base_url or config.GROQ_BASE_URL).rstrip("/")
        self._temperature = config.LLM_TEMPERATURE if temperature is None else temperature
        if not self._key:
            raise MissingAPIKey(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add a free "
                "key from https://console.groq.com -> API Keys."
            )
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
        resp = self._client.post(
            f"{self._base}/chat/completions",
            headers={"Authorization": f"Bearer {self._key}"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GroqLLM:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
