"""Health and readiness probes for production orchestration (K8s, load balancers)."""

from __future__ import annotations

import os

try:
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover
    class APIRouter:
        def __init__(self): pass
        def get(self, *_args, **_kwargs):
            def deco(fn): return fn
            return deco
    def JSONResponse(*_args, **_kwargs): ...

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness probe: process is running. Returns 200 with status ok."""
    return {"status": "ok"}


def _ready_check() -> tuple[bool, str]:
    """Return (ready, reason). When REVIEW_STORE=postgres, verifies DB connectivity."""
    if os.environ.get("REVIEW_STORE") != "postgres":
        return True, "ready"
    uri = os.environ.get("REVIEW_STORE_POSTGRES_URI") or os.environ.get("DATABASE_URL", "").strip()
    if not uri:
        return True, "ready"
    try:
        from obligation_runtime_lean_gateway.api.review_store_postgres import check_connection
        if check_connection(uri):
            return True, "ready"
    except Exception:
        pass
    return False, "database_unavailable"


@router.get("/ready")
def ready():
    """Readiness probe: service accepts traffic. When REVIEW_STORE=postgres, checks DB connectivity; returns 503 if unavailable."""
    is_ready, reason = _ready_check()
    if is_ready:
        return {"status": "ready"}
    return JSONResponse(
        content={"status": "not_ready", "reason": reason},
        status_code=503,
    )
