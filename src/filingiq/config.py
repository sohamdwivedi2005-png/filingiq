"""Runtime configuration, read from the environment with sensible defaults."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()  # load a local .env if present (see .env.example); real keys stay out of git

# --- SEC ---
# SEC blocks requests without a descriptive User-Agent that includes a contact.
SEC_USER_AGENT: str = os.getenv(
    "SEC_USER_AGENT", "FilingIQ research sohamdwivedi2005@gmail.com"
)
# SEC fair-access guidance is <= 10 requests/second. We stay well under it.
SEC_MIN_INTERVAL_SECONDS: float = float(os.getenv("SEC_MIN_INTERVAL_SECONDS", "0.15"))

# --- LLM (answer synthesis) ---
# Provider-agnostic: change LLM_PROVIDER without touching call sites.
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))

# Groq is OpenAI-compatible. Free key: https://console.groq.com -> API Keys.
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

# Ollama (OpenAI-compatible local endpoint) — for serving the fine-tuned model.
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
