"""Stable API error codes and response envelope for the Lean Gateway."""

from __future__ import annotations

import re

# Stable codes for client handling; do not remove or change semantics.
NOT_FOUND = "not_found"
VALIDATION_ERROR = "validation_error"
PATH_TRAVERSAL = "path_traversal"
SESSION_NOT_FOUND = "session_not_found"
REVIEW_NOT_FOUND = "review_not_found"
BAD_REQUEST = "bad_request"
INTERNAL_ERROR = "internal_error"


# Patterns for secret redaction (keys and values); values replaced with ***
_SECRET_KEYS = re.compile(
    r"(\b(?:DATABASE_URL|password|api_key|secret|token|LANGCHAIN_API_KEY)\s*[=:])\s*[^\s,\)\}\]\"]+",
    re.IGNORECASE,
)


def redact_secrets(text: str) -> str:
    """Replace secret values in text with *** so they are never logged or returned to clients."""
    if not text:
        return text
    return _SECRET_KEYS.sub(r"\1***", text)


def error_envelope(code: str, message: str, request_id: str = "req_local", details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "request_id": request_id, "details": details or {}}}


def _detail_code_and_message(detail: object) -> tuple[str, str]:
    """Extract (code, message) from HTTPException.detail (dict or str)."""
    if isinstance(detail, dict):
        code = detail.get("code", BAD_REQUEST)
        msg = detail.get("message", str(detail))
        return (code, msg)
    return (BAD_REQUEST, str(detail))
