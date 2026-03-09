from __future__ import annotations

import json
import urllib.request
from typing import Any


class ObligationRuntimeClient:
    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: dict[str, Any]) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:  # nosec - local/dev scaffold
            return json.loads(resp.read().decode("utf-8"))

    def _get(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        with urllib.request.urlopen(url) as resp:  # nosec - local/dev scaffold
            return json.loads(resp.read().decode("utf-8"))

    def open_environment(self, **payload: Any) -> dict:
        return self._post("/v1/environments/open", payload)

    def create_session(self, **payload: Any) -> dict:
        return self._post("/v1/sessions", payload)

    def apply_patch(self, session_id: str, **payload: Any) -> dict:
        return self._post(f"/v1/sessions/{session_id}/apply-patch", payload)

    def interactive_check(self, session_id: str, **payload: Any) -> dict:
        return self._post(f"/v1/sessions/{session_id}/interactive-check", payload)

    def get_goal(self, session_id: str, **payload: Any) -> dict:
        return self._post(f"/v1/sessions/{session_id}/goal", payload)

    def batch_verify(self, session_id: str, **payload: Any) -> dict:
        return self._post(f"/v1/sessions/{session_id}/batch-verify", payload)

    def get_review_payload(self, thread_id: str) -> dict:
        return self._get(f"/v1/reviews/{thread_id}")

    def submit_review_decision(self, thread_id: str, decision: str, **payload: Any) -> dict:
        return self._post(f"/v1/reviews/{thread_id}/{decision}", payload)
