"""Review API: pending review payload, approve/reject decisions, and resume (run graph from checkpoint)."""

from __future__ import annotations

import os

try:
    from fastapi import APIRouter, HTTPException, Request
except Exception:  # pragma: no cover
    class APIRouter:
        def __init__(self): pass
        def get(self, *_args, **_kwargs):
            def deco(fn): return fn
            return deco
        def post(self, *_args, **_kwargs):
            def deco(fn): return fn
            return deco
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str): ...
    class Request:
        pass

from obligation_runtime_schemas.api_paths import (
    PATH_REVIEWS,
    PATH_REVIEW_BY_THREAD,
    PATH_REVIEW_APPROVE,
    PATH_REVIEW_REJECT,
    PATH_REVIEW_RESUME,
)

from obligation_runtime_lean_gateway.api import deps

router = APIRouter()


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


@router.get(PATH_REVIEW_BY_THREAD)
def get_review(thread_id: str) -> dict:
    """Return review payload for a thread; 404 if not pending or unknown."""
    payload = deps.review_store.get_payload(thread_id)
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "review_not_found", "message": "Review not found"},
        )
    return payload


@router.post(PATH_REVIEWS)
def create_pending_review(payload: dict) -> dict:
    """Create or replace pending review (called by orchestrator on interrupt)."""
    thread_id = payload.get("thread_id")
    if not thread_id:
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "thread_id required"},
        )
    deps.review_store.put(thread_id, payload)
    return {"ok": True, "thread_id": thread_id}


@router.post(PATH_REVIEW_APPROVE)
def approve_review(thread_id: str, body: dict | None = None) -> dict:
    """Record approval for thread; 400 if not pending."""
    if not deps.review_store.set_decision(thread_id, "approved"):
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "No pending review for thread"},
        )
    return {"ok": True, "thread_id": thread_id, "decision": "approved"}


@router.post(PATH_REVIEW_REJECT)
def reject_review(thread_id: str, body: dict | None = None) -> dict:
    """Record rejection for thread; 400 if not pending."""
    if not deps.review_store.set_decision(thread_id, "rejected"):
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "No pending review for thread"},
        )
    return {"ok": True, "thread_id": thread_id, "decision": "rejected"}


@router.post(PATH_REVIEW_RESUME)
def resume_review(thread_id: str, request: Request) -> dict:
    """Resume the graph after approve/reject; requires a decision already set and a checkpointer."""
    rec = deps.review_store.get(thread_id)
    if rec is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "review_not_found", "message": "Review not found"},
        )
    decision = rec.get("decision")
    if decision not in ("approved", "rejected"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "bad_request",
                "message": "Approve or reject the review first, then call resume",
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
        from obligation_runtime_sdk.client import ObligationRuntimeClient
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "service_unavailable",
                "message": f"Resume requires obligation_runtime_orchestrator and sdk: {e!s}",
            },
        ) from e
    base_url = str(request.base_url).rstrip("/")
    client = ObligationRuntimeClient(base_url=base_url)
    graph = build_patch_admissibility_graph(client=client, checkpointer=checkpointer)
    resume_state = {
        "thread_id": thread_id,
        "obligation_id": "",
        "session_id": None,
        "environment_fingerprint": {},
        "obligation": {},
        "target_files": [],
        "target_declarations": [],
        "current_patch": {},
        "patch_history": [],
        "interactive_result": None,
        "goal_snapshots": [],
        "batch_result": None,
        "policy_decision": None,
        "trust_level": None,
        "approval_required": True,
        "approval_decision": decision,
        "status": "awaiting_approval",
        "attempt_count": 0,
        "max_attempts": 3,
        "artifacts": [],
        "trace_events": [],
        "_repo_path": "",
    }
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(resume_state, config=config)
    return {
        "ok": True,
        "thread_id": thread_id,
        "status": result.get("status"),
        "artifacts_count": len(result.get("artifacts") or []),
    }
