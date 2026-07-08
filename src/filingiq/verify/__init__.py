"""Numeric-verification loop: reconcile an answer's figures against XBRL facts."""

from filingiq.verify.loop import verify_answer
from filingiq.verify.verify import Verdict, verify_text

__all__ = ["Verdict", "verify_answer", "verify_text"]
