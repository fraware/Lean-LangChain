from __future__ import annotations

from pathlib import Path
from time import perf_counter

from lean_langchain_schemas.interactive import InteractiveCheckResult

from .normalizers import InteractiveNormalizer
from .session_manager import SessionLease, SessionManager
from .transport import LeanTransport
from .worker_pool import WorkerPool
from .worker_runner import run_with_timeout


class InteractiveAPI:
    def __init__(
        self,
        session_manager: SessionManager,
        worker_pool: WorkerPool,
        transport: LeanTransport | None = None,
        check_timeout_seconds: float = 300.0,
    ) -> None:
        self.session_manager = session_manager
        self.worker_pool = worker_pool
        self.normalizer = InteractiveNormalizer()
        if transport is None:
            raise ValueError(
                "transport is required; use set_test_transport(TestDoubleTransport()) only in tests"
            )
        self.transport = transport
        self.check_timeout_seconds = check_timeout_seconds

    def open_session(
        self, *, session_id: str, fingerprint_id: str, workspace_path: Path
    ) -> SessionLease:
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

        def _run() -> tuple[list, list, bool]:
            return self.transport.check(session_id, file_path)

        raw_diagnostics, raw_goals, ok = run_with_timeout(
            _run, timeout_seconds=self.check_timeout_seconds
        )
        elapsed_ms = int((perf_counter() - start) * 1000)
        return self.normalizer.result(
            ok=ok,
            diagnostics=raw_diagnostics,
            goals=raw_goals,
            timing_ms=elapsed_ms,
        )
