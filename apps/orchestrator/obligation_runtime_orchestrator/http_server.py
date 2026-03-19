"""Orchestrator HTTP API: resume and health/capability endpoints for gateway/service callers.

Run with: uvicorn obligation_runtime_orchestrator.http_server:app --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except Exception:  # pragma: no cover
    BaseModel = object  # type: ignore[misc, assignment]
    JSONResponse = dict  # type: ignore[misc, assignment]

from obligation_runtime_schemas.api_paths import PREFIX, PATH_REVIEW_RESUME
from obligation_runtime_schemas.orchestrator_api import (
    OrchestratorCapabilityBlock,
    OrchestratorHealthResponse,
    OrchestratorReadyResponse,
)

from obligation_runtime_orchestrator.orchestrator_capabilities import (
    compute_orchestrator_capabilities,
    log_orchestrator_capabilities,
)

_app: FastAPI | None = None


def _get_checkpointer():
    """Return PostgresSaver when CHECKPOINTER=postgres or DATABASE_URL set, else MemorySaver if available."""
    if os.environ.get("CHECKPOINTER") == "postgres" or os.environ.get("DATABASE_URL"):
        uri = os.environ.get("DATABASE_URL")
        if uri:
            try:
                from langgraph.checkpoint.postgres import PostgresSaver

                saver = PostgresSaver.from_conn_string(uri)
                saver.setup()
                return saver
            except ImportError:
                pass
    try:
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver()
    except ImportError:
        return None


def _fail_ready_on_degraded() -> bool:
    return os.environ.get("OBR_ORCHESTRATOR_READY_FAIL_ON_DEGRADED", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


class ResumeBody(BaseModel):
    """Request body for POST /v1/reviews/{thread_id}/resume."""

    decision: str


@asynccontextmanager
async def _lifespan(app: FastAPI):
    log = logging.getLogger("obligation_runtime_orchestrator")
    log_orchestrator_capabilities(log, app_version=getattr(app, "version", None) or "0.1.0")
    yield


def create_app() -> FastAPI:
    """Create the orchestrator FastAPI app (used by uvicorn and tests)."""
    from fastapi import APIRouter, FastAPI

    app = FastAPI(
        title="Obligation Runtime Orchestrator",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=_lifespan,
    )

    @app.get("/health", response_model=OrchestratorHealthResponse, tags=["health"])
    def health() -> OrchestratorHealthResponse:
        snap = compute_orchestrator_capabilities()
        return OrchestratorHealthResponse(
            status="ok",
            version=app.version,
            degraded=snap["degraded"],
            degraded_reasons=snap["degraded_reasons"],
            capabilities=OrchestratorCapabilityBlock(
                checkpointer=snap["checkpointer"],
                policy_pack_ref=snap["policy_pack_ref"],
                gateway_url_configured=snap["gateway_url_configured"],
                langgraph_runtime=snap["langgraph_runtime"],
            ),
        )

    @app.get("/ready", tags=["health"])
    def ready():
        snap = compute_orchestrator_capabilities()
        cp = _get_checkpointer()
        ready_ok = cp is not None
        block = OrchestratorReadyResponse(
            status="ready",
            version=app.version,
            degraded=snap["degraded"],
            degraded_reasons=snap["degraded_reasons"],
            capabilities=OrchestratorCapabilityBlock(
                checkpointer=snap["checkpointer"],
                policy_pack_ref=snap["policy_pack_ref"],
                gateway_url_configured=snap["gateway_url_configured"],
                langgraph_runtime=snap["langgraph_runtime"],
            ),
        )
        if _fail_ready_on_degraded() and snap["degraded"]:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": "degraded_capabilities",
                    "details": block.model_dump(mode="json"),
                },
            )
        if not ready_ok:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": "checkpointer_unavailable",
                    **block.model_dump(mode="json"),
                },
            )
        return block.model_dump(mode="json")

    router = APIRouter()

    @router.post(PATH_REVIEW_RESUME)
    def resume(thread_id: str, body: ResumeBody) -> dict:
        """Resume the patch-admissibility graph after approve/reject. Requires checkpointer."""
        decision = (body.decision or "").strip().lower()
        if decision not in ("approved", "rejected"):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "bad_request",
                    "message": "decision must be 'approved' or 'rejected'",
                },
            )
        checkpointer = _get_checkpointer()
        if checkpointer is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "service_unavailable",
                    "message": "Resume requires a checkpointer (set CHECKPOINTER=postgres and DATABASE_URL)",
                },
            )
        try:
            from obligation_runtime_orchestrator.runtime.graph import (
                build_patch_admissibility_graph,
            )
            from obligation_runtime_orchestrator.runtime.initial_state import make_resume_state
        except ImportError as e:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "service_unavailable",
                    "message": f"Orchestrator runtime not available: {e!s}",
                },
            ) from e
        gateway_base_url = os.environ.get("OBR_GATEWAY_URL", "http://localhost:8000")
        graph = build_patch_admissibility_graph(
            gateway_base_url=gateway_base_url,
            checkpointer=checkpointer,
        )
        resume_state = make_resume_state(thread_id=thread_id, decision=decision)
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke(resume_state, config=config)
        return {
            "ok": True,
            "thread_id": thread_id,
            "status": result.get("status"),
            "artifacts_count": len(result.get("artifacts") or []),
        }

    app.include_router(router, prefix=PREFIX)
    return app


def get_app() -> FastAPI:
    global _app
    if _app is None:
        _app = create_app()
    return _app


app = get_app()
