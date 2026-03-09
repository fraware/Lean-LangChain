from __future__ import annotations

from pathlib import Path
from time import perf_counter

from obligation_runtime_schemas.interactive import InteractiveCheckResult

from .normalizers import InteractiveNormalizer
from .session_manager import SessionLease, SessionManager
from .worker_pool import WorkerPool


class InteractiveAPI:
    def __init__(self, session_manager: SessionManager, worker_pool: WorkerPool) -> None:
        self.session_manager = session_manager
        self.worker_pool = worker_pool
        self.normalizer = InteractiveNormalizer()

    def open_session(self, *, session_id: str, fingerprint_id: str, workspace_path: Path) -> SessionLease:
        lease = SessionLease(
            session_id=session_id,
            fingerprint_id=fingerprint_id,
            workspace_path=workspace_path,
            started_at=perf_counter(),
            last_used_at=perf_counter(),
        )
        self.session_manager.register(lease)
        self.worker_pool.acquire(fingerprint_id, workspace_path)
        return lease

    def check_interactive(self, *, session_id: str, file_path: str) -> InteractiveCheckResult:
        lease = self.session_manager.get(session_id)
        lease.touch()

        start = perf_counter()

        # Placeholder transport. Replace with actual Lean server/LSP integration.
        raw_diagnostics: list[dict] = []
        raw_goals: list[dict] = []
        ok = True

        elapsed_ms = int((perf_counter() - start) * 1000)
        return self.normalizer.result(
            ok=ok,
            diagnostics=raw_diagnostics,
            goals=raw_goals,
            timing_ms=elapsed_ms,
        )
