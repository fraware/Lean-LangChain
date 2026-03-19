"""Health and readiness probes for production orchestration (K8s, load balancers)."""

from __future__ import annotations

import os
from typing import Any

try:
    from fastapi import APIRouter, Request
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover
    from lean_langchain_gateway.api.fastapi_shim import (  # type: ignore[assignment]
        APIRouter,
        JSONResponse,
        Request,
    )

from lean_langchain_schemas.gateway_api import (
    GatewayCapabilityBlock,
    GatewayHealthResponse,
    GatewayReadyOkResponse,
)

from lean_langchain_gateway.api.capabilities import compute_capability_snapshot

router = APIRouter(tags=["health"])


def _cap_block(snap: dict[str, Any]) -> GatewayCapabilityBlock:
    return GatewayCapabilityBlock(
        lean_interactive=snap["lean_interactive"],
        axiom_audit=snap["axiom_audit"],
        fresh_checker=snap["fresh_checker"],
        review_store=snap["review_store"],
    )


@router.get("/health", response_model=GatewayHealthResponse)
def health(request: Request) -> GatewayHealthResponse:
    """Liveness probe: process is running; includes capability snapshot for operators."""
    ver = getattr(getattr(request, "app", None), "version", None) or "0.1.0"
    snap = compute_capability_snapshot()
    return GatewayHealthResponse(
        status="ok",
        version=ver,
        degraded=snap["degraded"],
        capabilities=_cap_block(snap),
    )


def _ready_check() -> tuple[bool, str]:
    """Return (ready, reason). When REVIEW_STORE=postgres, verifies DB connectivity."""
    if os.environ.get("REVIEW_STORE") != "postgres":
        return True, "ready"
    uri = os.environ.get("REVIEW_STORE_POSTGRES_URI") or os.environ.get("DATABASE_URL", "").strip()
    if not uri:
        return True, "ready"
    try:
        from lean_langchain_gateway.api.review_store_postgres import check_connection

        if check_connection(uri):
            return True, "ready"
    except Exception:
        pass
    return False, "database_unavailable"


def _fail_on_degraded() -> bool:
    return os.environ.get("OBR_READY_FAIL_ON_DEGRADED", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


@router.get("/ready", response_model=None)
def ready(request: Request) -> dict[str, Any] | JSONResponse:
    """Readiness: DB when postgres; optional 503 if OBR_READY_FAIL_ON_DEGRADED and capabilities degraded."""
    is_ready, reason = _ready_check()
    snap = compute_capability_snapshot()
    ver = getattr(getattr(request, "app", None), "version", None) or "0.1.0"
    ok_body = GatewayReadyOkResponse(
        status="ready",
        version=ver,
        degraded=snap["degraded"],
        degraded_reasons=snap["degraded_reasons"],
        capabilities=_cap_block(snap),
    )
    if _fail_on_degraded() and snap["degraded"]:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": "degraded_capabilities",
                "details": ok_body.model_dump(mode="json"),
            },
        )
    if not is_ready:
        body = {
            "status": "not_ready",
            "reason": reason,
            **ok_body.model_dump(mode="json"),
        }
        return JSONResponse(content=body, status_code=503)
    return ok_body.model_dump(mode="json")
