"""Obligation Runtime Python SDK: Gateway API client with httpx, timeouts, structured errors."""

from __future__ import annotations

import json
from typing import Any, Callable

import httpx

from obligation_runtime_schemas.api_paths import (
    PREFIX,
    PATH_ENVIRONMENTS_OPEN,
    PATH_REVIEWS,
    PATH_REVIEW_APPROVE,
    PATH_REVIEW_BY_THREAD,
    PATH_REVIEW_REJECT,
    PATH_REVIEW_RESUME,
    PATH_SESSION_APPLY_PATCH,
    PATH_SESSION_BATCH_VERIFY,
    PATH_SESSION_DEFINITION,
    PATH_SESSION_GOAL,
    PATH_SESSION_HOVER,
    PATH_SESSION_INTERACTIVE_CHECK,
    PATH_SESSIONS,
    path_review,
    path_session,
)

from obligation_runtime_sdk.exceptions import ObligationRuntimeAPIError

RequestAdapter = Callable[[str, str, Any | None], dict]

DEFAULT_TIMEOUT = 60.0
BATCH_VERIFY_TIMEOUT = 120.0


def _parse_error_response(status_code: int, body: bytes | None) -> tuple[str, str]:
    """Extract code and message from Gateway error envelope. Returns (code, message)."""
    code = "unknown"
    message = f"HTTP {status_code}"
    if body:
        try:
            data = json.loads(body.decode("utf-8"))
            err = data.get("error") if isinstance(data, dict) else None
            if isinstance(err, dict):
                code = err.get("code", code)
                message = err.get("message", message)
        except (ValueError, UnicodeDecodeError):
            message = body.decode("utf-8", errors="replace")[:500]
    return code, message


class ObligationRuntimeClient:
    """Sync client for the Obligation Runtime Gateway API.

    Uses httpx with configurable timeouts. When request_adapter is provided
    (e.g. in tests), HTTP is bypassed and the adapter is called instead.

    Example:
        with ObligationRuntimeClient(base_url="http://localhost:8000") as client:
            env = client.open_environment(repo_id="my-repo", repo_path="/path")
            session = client.create_session(
                fingerprint_id=env["fingerprint_id"]
            )
            result = client.batch_verify(
                session_id=session["session_id"], ...
            )
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        request_adapter: RequestAdapter | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        batch_verify_timeout: float = BATCH_VERIFY_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._request_adapter = request_adapter
        self._timeout = timeout
        self._batch_verify_timeout = batch_verify_timeout
        self._client: httpx.Client | None = None

    def _http_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=httpx.Timeout(self._timeout),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def _post(
        self,
        path: str,
        payload: dict[str, Any],
        timeout: float | None = None,
    ) -> dict:
        if self._request_adapter is not None:
            return self._request_adapter("POST", path, payload)
        client = self._http_client()
        to = timeout if timeout is not None else self._timeout
        resp = client.post(path, json=payload, timeout=to)
        if resp.status_code >= 400:
            code, message = _parse_error_response(
                resp.status_code, resp.content
            )
            try:
                body = resp.json() if resp.content else {}
            except Exception:
                body = {}
            raise ObligationRuntimeAPIError(
                resp.status_code,
                message,
                code=code,
                body=body,
            )
        return resp.json()

    def _get(self, path: str) -> dict:
        if self._request_adapter is not None:
            return self._request_adapter("GET", path, None)
        client = self._http_client()
        resp = client.get(path)
        if resp.status_code >= 400:
            code, message = _parse_error_response(
                resp.status_code, resp.content
            )
            try:
                body = resp.json() if resp.content else {}
            except Exception:
                body = {}
            raise ObligationRuntimeAPIError(
                resp.status_code,
                message,
                code=code,
                body=body,
            )
        return resp.json()

    def __enter__(self) -> ObligationRuntimeClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Release HTTP resources. No-op when using a request_adapter."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def open_environment(self, **payload: Any) -> dict:
        return self._post(PREFIX + PATH_ENVIRONMENTS_OPEN, payload)

    def create_session(self, **payload: Any) -> dict:
        return self._post(PREFIX + PATH_SESSIONS, payload)

    def apply_patch(self, session_id: str, **payload: Any) -> dict:
        return self._post(
            path_session(session_id, PATH_SESSION_APPLY_PATCH),
            payload,
        )

    def interactive_check(self, session_id: str, **payload: Any) -> dict:
        return self._post(
            path_session(session_id, PATH_SESSION_INTERACTIVE_CHECK),
            payload,
        )

    def get_goal(self, session_id: str, **payload: Any) -> dict:
        return self._post(
            path_session(session_id, PATH_SESSION_GOAL),
            payload,
        )

    def hover(self, session_id: str, **payload: Any) -> dict:
        return self._post(
            path_session(session_id, PATH_SESSION_HOVER),
            payload,
        )

    def definition(self, session_id: str, **payload: Any) -> dict:
        return self._post(
            path_session(session_id, PATH_SESSION_DEFINITION),
            payload,
        )

    def batch_verify(self, session_id: str, **payload: Any) -> dict:
        return self._post(
            path_session(session_id, PATH_SESSION_BATCH_VERIFY),
            payload,
            timeout=self._batch_verify_timeout,
        )

    def get_review_payload(self, thread_id: str) -> dict:
        return self._get(path_review(thread_id, PATH_REVIEW_BY_THREAD))

    def create_pending_review(self, payload: dict[str, Any]) -> dict:
        """Push review payload to Gateway (e.g. graph interrupt_for_approval)."""
        return self._post(PREFIX + PATH_REVIEWS, payload)

    def submit_review_decision(
        self,
        thread_id: str,
        decision: str,
        **payload: Any,
    ) -> dict:
        if decision == "approve":
            path = path_review(thread_id, PATH_REVIEW_APPROVE)
        elif decision == "reject":
            path = path_review(thread_id, PATH_REVIEW_REJECT)
        else:
            path = (
                path_review(thread_id, PATH_REVIEW_BY_THREAD)
                + f"/{decision}"
            )
        return self._post(path, payload or {})

    def resume(self, thread_id: str) -> dict:
        """Resume graph after approve/reject. Needs checkpointer (e.g. Postgres)."""
        return self._post(path_review(thread_id, PATH_REVIEW_RESUME), {})
