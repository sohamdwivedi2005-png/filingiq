"""Provider-agnostic LLM access. Swap providers via config.LLM_PROVIDER."""

from __future__ import annotations

from filingiq import config
from filingiq.llm.base import LLM, Message

__all__ = ["LLM", "Message", "get_llm"]


def get_llm(provider: str | None = None, **kwargs) -> LLM:
    """Return an LLM client for the configured (or requested) provider."""
    provider = provider or config.LLM_PROVIDER
    if provider == "groq":
        from filingiq.llm.groq import GroqLLM

        return GroqLLM(**kwargs)
    if provider == "ollama":
        from filingiq.llm.ollama import OllamaLLM

        return OllamaLLM(**kwargs)
    raise ValueError(f"Unknown LLM provider: {provider!r}")
