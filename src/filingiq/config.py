"""Runtime configuration, read from the environment with sensible defaults."""

from __future__ import annotations

import os

# SEC blocks requests without a descriptive User-Agent that includes a contact.
# Override in a local .env (see .env.example) or the shell environment.
SEC_USER_AGENT: str = os.getenv(
    "SEC_USER_AGENT", "FilingIQ research sohamdwivedi2005@gmail.com"
)

# SEC fair-access guidance is <= 10 requests/second. We stay well under it.
SEC_MIN_INTERVAL_SECONDS: float = float(os.getenv("SEC_MIN_INTERVAL_SECONDS", "0.15"))
