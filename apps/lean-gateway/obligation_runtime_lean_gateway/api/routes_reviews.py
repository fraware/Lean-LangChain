"""Review API: pending review payload, approve/reject decisions, and resume (run graph from checkpoint).

Resume is delegated to the orchestrator service via OBR_ORCHESTRATOR_URL. The gateway does not
import orchestrator runtime modules; it calls the orchestrator HTTP API.
"""

from __future__ import annotations

import os

try:
    from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
except Exception:  # pragma: no cover
    class APIRouter:
        def __init__(self): pass
        def get(self, *_args, **_kwargs):
            def deco(fn): return fn
            return deco
        def post(self, *_args, **_kwargs):
            def deco(fn): return fn
            return deco
    class BackgroundTasks:
        def add_task(self, *args, **kwargs): pass
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
from obligation_runtime_lean_gateway.api.webhooks import (
    notify_review_created,
    notify_review_decision,
    notify_review_resumed,
)

router = APIRouter()


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
def create_pending_review(payload: dict, background_tasks: BackgroundTasks) -> dict:
    """Create or replace pending review (called by orchestrator on interrupt)."""
    thread_id = payload.get("thread_id")
    if not thread_id:
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "thread_id required"},
        )
    deps.review_store.put(thread_id, payload)
    background_tasks.add_task(notify_review_created, thread_id, payload)
    return {"ok": True, "thread_id": thread_id}


@router.post(PATH_REVIEW_APPROVE)
def approve_review(thread_id: str, background_tasks: BackgroundTasks, body: dict | None = None) -> dict:
    """Record approval for thread; 400 if not pending."""
    if not deps.review_store.set_decision(thread_id, "approved"):
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "No pending review for thread"},
        )
    background_tasks.add_task(notify_review_decision, thread_id, "approved")
    return {"ok": True, "thread_id": thread_id, "decision": "approved"}


@router.post(PATH_REVIEW_REJECT)
def reject_review(thread_id: str, background_tasks: BackgroundTasks, body: dict | None = None) -> dict:
    """Record rejection for thread; 400 if not pending."""
    if not deps.review_store.set_decision(thread_id, "rejected"):
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "No pending review for thread"},
        )
    background_tasks.add_task(notify_review_decision, thread_id, "rejected")
    return {"ok": True, "thread_id": thread_id, "decision": "rejected"}


@router.post(PATH_REVIEW_RESUME)
def resume_review(thread_id: str, request: Request, background_tasks: BackgroundTasks) -> dict:
    """Resume the graph after approve/reject by calling the orchestrator service."""
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
    orchestrator_url = (os.environ.get("OBR_ORCHESTRATOR_URL") or "").rstrip("/")
    if not orchestrator_url:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "service_unavailable",
                "message": "Resume requires OBR_ORCHESTRATOR_URL (orchestrator service base URL)",
            },
        )
    import httpx
    resume_path = f"/v1/reviews/{thread_id}/resume"
    url = f"{orchestrator_url}{resume_path}"
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json={"decision": decision})
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "service_unavailable",
                "message": f"Orchestrator request failed: {e!s}",
            },
        ) from e
    if response.status_code != 200:
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"message": response.text}
        detail = body.get("detail", body) if isinstance(body, dict) else {"message": response.text}
        raise HTTPException(status_code=response.status_code, detail=detail)
    result = response.json()
    if isinstance(result, dict):
        background_tasks.add_task(
            notify_review_resumed,
            thread_id,
            result.get("status", ""),
            result.get("artifacts_count", 0),
        )
    return result
