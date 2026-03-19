"""Gateway dependencies: real implementations only in production; tests inject via set_test_*."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from lean_langchain_gateway.environment.fingerprint import FingerprintService
from lean_langchain_gateway.environment.snapshot_store import SnapshotStore
from lean_langchain_gateway.environment.overlay_fs import OverlayFS
from lean_langchain_gateway.server.session_manager import SessionManager
from lean_langchain_gateway.server.worker_pool import WorkerPool
from lean_langchain_gateway.server.interactive_api import InteractiveAPI
from lean_langchain_gateway.server.runner import get_runner
from lean_langchain_gateway.server.transport import (
    LspLeanTransport,
    SubprocessLeanTransport,
    LeanTransport,
)
from lean_langchain_gateway.api.review_store import InMemoryReviewStore
from lean_langchain_gateway.api.review_store_postgres import PostgresReviewStore
from lean_langchain_gateway.batch.build_runner import BuildRunner
from lean_langchain_gateway.batch.axiom_audit import AxiomAuditorReal
from lean_langchain_gateway.batch.fresh_checker import FreshCheckerReal

_DATA_ROOT = Path(".var")

fingerprints = FingerprintService()
snapshots = SnapshotStore(_DATA_ROOT)
overlays = OverlayFS(_DATA_ROOT)
session_manager = SessionManager()
worker_pool = WorkerPool()
_interactive_runner = get_runner("interactive")
_batch_runner = get_runner("batch")

# Test-only injection: set by tests before using the gateway; production never sets these.
_test_transport: LeanTransport | None = None
_test_axiom_auditor: Any = None
_test_fresh_checker: Any = None
_cached_transport: LeanTransport | None = None
_cached_interactive_api: InteractiveAPI | None = None
_cached_axiom_auditor: Any = None
_cached_fresh_checker: Any = None


def set_test_transport(transport: LeanTransport) -> None:
    """Inject transport for tests only. Production must not call this."""
    global _test_transport
    _test_transport = transport


def set_test_axiom_auditor(auditor: Any) -> None:
    """Inject axiom auditor for tests only. Production must not call this."""
    global _test_axiom_auditor
    _test_axiom_auditor = auditor


def set_test_fresh_checker(checker: Any) -> None:
    """Inject fresh checker for tests only. Production must not call this."""
    global _test_fresh_checker
    _test_fresh_checker = checker


def _resolve_lean_transport() -> LeanTransport:
    """Resolve interactive Lean transport. Raises if not configured (production requires real)."""
    if os.environ.get("OBR_USE_LEAN_LSP"):
        return LspLeanTransport(session_manager)
    if os.environ.get("OBR_USE_REAL_LEAN"):
        return SubprocessLeanTransport(session_manager, runner=_interactive_runner)
    raise RuntimeError("Set OBR_USE_REAL_LEAN or OBR_USE_LEAN_LSP for the interactive lane.")


def _resolve_axiom_auditor() -> AxiomAuditorReal:
    """Resolve axiom auditor. Raises if not configured (production requires real)."""
    if os.environ.get("OBR_USE_REAL_AXIOM_AUDIT"):
        return AxiomAuditorReal(runner=_batch_runner)
    raise RuntimeError("Set OBR_USE_REAL_AXIOM_AUDIT for batch-verify (axiom audit).")


def _resolve_fresh_checker() -> FreshCheckerReal:
    """Resolve fresh checker. Raises if not configured (production requires real)."""
    if os.environ.get("OBR_USE_REAL_FRESH_CHECKER"):
        return FreshCheckerReal(runner=_batch_runner)
    raise RuntimeError("Set OBR_USE_REAL_FRESH_CHECKER for batch-verify (fresh check).")


def _get_lean_transport() -> LeanTransport:
    if _test_transport is not None:
        return _test_transport
    global _cached_transport
    if _cached_transport is None:
        _cached_transport = _resolve_lean_transport()
    return _cached_transport


def _get_axiom_auditor() -> Any:
    if _test_axiom_auditor is not None:
        return _test_axiom_auditor
    global _cached_axiom_auditor
    if _cached_axiom_auditor is None:
        _cached_axiom_auditor = _resolve_axiom_auditor()
    return _cached_axiom_auditor


def _get_fresh_checker() -> Any:
    if _test_fresh_checker is not None:
        return _test_fresh_checker
    global _cached_fresh_checker
    if _cached_fresh_checker is None:
        _cached_fresh_checker = _resolve_fresh_checker()
    return _cached_fresh_checker


def _get_interactive_api() -> InteractiveAPI:
    global _cached_interactive_api
    if _test_transport is not None:
        return InteractiveAPI(session_manager, worker_pool, transport=_test_transport)
    if _cached_interactive_api is None:
        _cached_interactive_api = InteractiveAPI(
            session_manager, worker_pool, transport=_get_lean_transport()
        )
    return _cached_interactive_api


def __getattr__(name: str) -> Any:
    """Resolve interactive_api, axiom_auditor, fresh_checker (real in production; tests inject via set_test_*)."""
    if name == "interactive_api":
        return _get_interactive_api()
    if name == "axiom_auditor":
        return _get_axiom_auditor()
    if name == "fresh_checker":
        return _get_fresh_checker()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# These are always resolved at import (no test override).
def _review_store() -> Any:
    store_backend = os.environ.get("REVIEW_STORE", "memory")
    if store_backend == "postgres":
        uri = os.environ.get("REVIEW_STORE_POSTGRES_URI") or os.environ.get("DATABASE_URL")
        if uri:
            return PostgresReviewStore(uri)
    return InMemoryReviewStore()


review_store = _review_store()
build_runner = BuildRunner(runner=_batch_runner)
