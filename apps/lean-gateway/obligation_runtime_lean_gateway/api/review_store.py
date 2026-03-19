"""Review store: in-memory (default) or Postgres backend. Protocol for put/get/set_decision/delete."""

from __future__ import annotations

from typing import Any, Literal, Mapping, Protocol


class ReviewStoreProtocol(Protocol):
    """Thread-scoped pending reviews: payload + optional decision after approve/reject."""

    def put(self, thread_id: str, payload: Mapping[str, Any]) -> None:
        """Create or replace pending review for thread_id. Clears any prior decision."""
        ...

    def get(self, thread_id: str) -> dict | None:
        """Return full record (payload + decision) or None if not found."""
        ...

    def get_payload(self, thread_id: str) -> dict | None:
        """Return only the review payload for GET /reviews/{id}; None if not found."""
        ...

    def set_decision(
        self,
        thread_id: str,
        decision: Literal["approved", "rejected"],
    ) -> bool:
        """Record approve/reject. Returns True if thread had a pending review."""
        ...

    def delete(self, thread_id: str) -> bool:
        """Remove review (e.g. after resume). Returns True if existed."""
        ...


class InMemoryReviewStore:
    """In-memory implementation. Default for dev and CI."""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def put(self, thread_id: str, payload: Mapping[str, Any]) -> None:
        self._store[thread_id] = {"payload": dict(payload), "decision": None}

    def get(self, thread_id: str) -> dict | None:
        return dict(self._store[thread_id]) if thread_id in self._store else None

    def get_payload(self, thread_id: str) -> dict | None:
        rec = self.get(thread_id)
        if rec is None:
            return None
        out = dict(rec["payload"])
        if rec.get("decision") is not None:
            out["status"] = rec["decision"]
        return out

    def set_decision(
        self,
        thread_id: str,
        decision: Literal["approved", "rejected"],
    ) -> bool:
        if thread_id not in self._store:
            return False
        self._store[thread_id]["decision"] = decision
        return True

    def delete(self, thread_id: str) -> bool:
        if thread_id in self._store:
            del self._store[thread_id]
            return True
        return False


# Backward compatibility: ReviewStore is the in-memory implementation.
ReviewStore = InMemoryReviewStore
