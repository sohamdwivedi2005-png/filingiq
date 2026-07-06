"""Local persistence so ingestion runs don't re-hit SEC each time."""

from filingiq.store import db

__all__ = ["db"]
