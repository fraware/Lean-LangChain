from __future__ import annotations

import json
import urllib.request
from typing import Any, Callable

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

RequestAdapter = Callable[[str, str, Any | None], dict]


class ObligationRuntimeClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        request_adapter: RequestAdapter | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._request_adapter = request_adapter

    def _post(self, path: str, payload: dict[str, Any]) -> dict:
        if self._request_adapter is not None:
            return self._request_adapter("POST", path, payload)
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:  # nosec - local/dev scaffold
            return json.loads(resp.read().decode("utf-8"))

    def _get(self, path: str) -> dict:
        if self._request_adapter is not None:
            return self._request_adapter("GET", path, None)
        url = f"{self.base_url}{path}"
        with urllib.request.urlopen(url) as resp:  # nosec - local/dev scaffold
            return json.loads(resp.read().decode("utf-8"))

    def open_environment(self, **payload: Any) -> dict:
        return self._post(PREFIX + PATH_ENVIRONMENTS_OPEN, payload)

    def create_session(self, **payload: Any) -> dict:
        return self._post(PREFIX + PATH_SESSIONS, payload)

    def apply_patch(self, session_id: str, **payload: Any) -> dict:
        return self._post(path_session(session_id, PATH_SESSION_APPLY_PATCH), payload)

    def interactive_check(self, session_id: str, **payload: Any) -> dict:
        return self._post(path_session(session_id, PATH_SESSION_INTERACTIVE_CHECK), payload)

    def get_goal(self, session_id: str, **payload: Any) -> dict:
        return self._post(path_session(session_id, PATH_SESSION_GOAL), payload)

    def hover(self, session_id: str, **payload: Any) -> dict:
        return self._post(path_session(session_id, PATH_SESSION_HOVER), payload)

    def definition(self, session_id: str, **payload: Any) -> dict:
        return self._post(path_session(session_id, PATH_SESSION_DEFINITION), payload)

    def batch_verify(self, session_id: str, **payload: Any) -> dict:
        return self._post(path_session(session_id, PATH_SESSION_BATCH_VERIFY), payload)

    def get_review_payload(self, thread_id: str) -> dict:
        return self._get(path_review(thread_id, PATH_REVIEW_BY_THREAD))

    def create_pending_review(self, payload: dict[str, Any]) -> dict:
        """Push review payload to Gateway (e.g. when graph hits interrupt_for_approval)."""
        return self._post(PREFIX + PATH_REVIEWS, payload)

    def submit_review_decision(self, thread_id: str, decision: str, **payload: Any) -> dict:
        if decision == "approve":
            path = path_review(thread_id, PATH_REVIEW_APPROVE)
        elif decision == "reject":
            path = path_review(thread_id, PATH_REVIEW_REJECT)
        else:
            path = path_review(thread_id, PATH_REVIEW_BY_THREAD) + f"/{decision}"
        return self._post(path, payload or {})

    def resume(self, thread_id: str) -> dict:
        """Resume the graph after approve/reject. Requires a checkpointer (e.g. Postgres)."""
        return self._post(path_review(thread_id, PATH_REVIEW_RESUME), {})
