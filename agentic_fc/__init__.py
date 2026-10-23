"""Agentic FC: offline football decision engine (no AWS deployment)."""
from .policy import decide, decide_payload

__all__ = ["decide", "decide_payload"]
