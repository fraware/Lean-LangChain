"""Exceptions raised by the Obligation Runtime SDK."""

from __future__ import annotations


class ObligationRuntimeError(Exception):
    """Base exception for SDK errors."""

    pass


class ObligationRuntimeAPIError(ObligationRuntimeError):
    """Raised when the Gateway returns an error response (4xx or 5xx).

    Attributes:
        status_code: HTTP status code.
        code: Gateway error code (e.g. session_not_found, review_not_found).
        message: Human-readable message from the Gateway.
        body: Raw response body (dict if JSON, else None).
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        code: str | None = None,
        body: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code or "unknown"
        self.message = message
        self.body = body or {}
        super().__init__(f"[{status_code}] {self.code}: {message}")
