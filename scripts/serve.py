"""Run the FilingIQ web app.

    uv run python scripts/serve.py            # http://127.0.0.1:8000
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import uvicorn  # noqa: E402

from filingiq.api.app import app  # noqa: E402

if __name__ == "__main__":
    # HOST/PORT come from the environment in containers (HF Spaces uses 7860).
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")
