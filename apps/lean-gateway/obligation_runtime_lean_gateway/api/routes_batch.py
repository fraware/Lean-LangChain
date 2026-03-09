from __future__ import annotations

try:
    from fastapi import APIRouter
except Exception:  # pragma: no cover
    class APIRouter:
        def __init__(self): pass
        def post(self, *_args, **_kwargs):
            def deco(fn): return fn
            return deco

from obligation_runtime_lean_gateway.api import deps
from obligation_runtime_lean_gateway.batch.combine import combine_batch_results

router = APIRouter()


@router.post("/sessions/{session_id}/batch-verify")
def batch_verify(session_id: str, payload: dict) -> dict:
    lease = deps.session_manager.get(session_id)
    build = deps.build_runner.run(lease.workspace_path)
    audit = deps.axiom_auditor.run(lease.workspace_path, payload.get("target_declarations", []))
    fresh = deps.fresh_checker.run(lease.workspace_path)
    combined = combine_batch_results(build, audit, fresh)
    return combined.model_dump(mode="json")
