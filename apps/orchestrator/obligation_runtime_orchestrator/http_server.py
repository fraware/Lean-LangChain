"""Orchestrator HTTP API: resume and other service endpoints for gateway/service callers.

Gateway calls this service for review resume instead of importing graph internals.
Run with: uvicorn obligation_runtime_orchestrator.http_server:app --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

import os

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except Exception:  # pragma: no cover
    BaseModel = object  # type: ignore[misc, assignment]

from obligation_runtime_schemas.api_paths import PREFIX, PATH_REVIEW_RESUME

# Lazy imports for graph/checkpointer so CLI-only installs are not forced to load them
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


class ResumeBody(BaseModel):
    """Request body for POST /v1/reviews/{thread_id}/resume."""
    decision: str  # "approved" | "rejected"


def create_app() -> FastAPI:
    """Create the orchestrator FastAPI app (used by uvicorn and tests)."""
    from fastapi import APIRouter, FastAPI
    app = FastAPI(
        title="Obligation Runtime Orchestrator",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    router = APIRouter()

    # POST /v1/reviews/{thread_id}/resume — resume graph after human approval
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
            from obligation_runtime_orchestrator.runtime.graph import build_patch_admissibility_graph
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
    """Return the singleton app (for uvicorn)."""
    global _app
    if _app is None:
        _app = create_app()
    return _app


app = get_app()
