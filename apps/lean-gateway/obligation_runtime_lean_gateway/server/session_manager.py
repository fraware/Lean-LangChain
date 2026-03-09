from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic


@dataclass(slots=True)
class SessionLease:
    session_id: str
    fingerprint_id: str
    workspace_path: Path
    started_at: float
    last_used_at: float

    def touch(self) -> None:
        self.last_used_at = monotonic()


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionLease] = {}

    def register(self, lease: SessionLease) -> None:
        self._sessions[lease.session_id] = lease

    def get(self, session_id: str) -> SessionLease:
        return self._sessions[session_id]

    def release(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
