"""Structured logging configuration for the Gateway: JSON format, request_id, log level from env."""

from __future__ import annotations

import json
import logging
import os
from contextvars import ContextVar
from datetime import datetime, timezone

# Set in middleware; read by formatter so every log line can include request_id.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

def _log_level() -> int:
    raw = os.environ.get("OBR_LOG_LEVEL") or os.environ.get("LOG_LEVEL", "INFO")
    return getattr(logging, str(raw).upper(), logging.INFO)


class JsonFormatter(logging.Formatter):
    """Format log records as one JSON object per line with timestamp, level, message, request_id."""

    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        rid = getattr(record, "request_id", None) or request_id_ctx.get("")
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": msg,
        }
        if rid:
            payload["request_id"] = rid
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    """Configure root logger: JSON formatter, level from OBR_LOG_LEVEL/LOG_LEVEL."""
    level = _log_level()
    formatter = JsonFormatter()
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root.addHandler(handler)
    else:
        for h in root.handlers:
            h.setFormatter(formatter)
            h.setLevel(level)
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).setLevel(level)
