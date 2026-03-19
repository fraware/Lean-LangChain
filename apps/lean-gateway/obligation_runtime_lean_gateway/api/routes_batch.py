from __future__ import annotations

import os

try:
    from fastapi import APIRouter, HTTPException
except Exception:  # pragma: no cover
    from obligation_runtime_lean_gateway.api.fastapi_shim import (  # type: ignore[assignment]
        APIRouter,
        HTTPException,
    )

from obligation_runtime_schemas.api_paths import PATH_SESSION_BATCH_VERIFY
from obligation_runtime_schemas.batch import BatchVerifyResult
from obligation_runtime_schemas.gateway_api import BatchVerifyRequest

from obligation_runtime_lean_gateway.api import deps
from obligation_runtime_lean_gateway.batch.axiom_audit import AxiomAuditorReal
from obligation_runtime_lean_gateway.batch.combine import (
    apply_acceptance_strict,
    combine_batch_results,
)
from obligation_runtime_lean_gateway.batch.fresh_checker import FreshCheckerReal

router = APIRouter()


@router.post(PATH_SESSION_BATCH_VERIFY, response_model=BatchVerifyResult)
def batch_verify(session_id: str, payload: BatchVerifyRequest) -> BatchVerifyResult:
    try:
        lease = deps.session_manager.get(session_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail={"code": "session_not_found", "message": "Session not found"},
        )
    build = deps.build_runner.run(lease.workspace_path)
    audit = deps.axiom_auditor.run(lease.workspace_path, payload.target_declarations)
    fresh = deps.fresh_checker.run(lease.workspace_path)
    axiom_evidence_real = isinstance(deps.axiom_auditor, AxiomAuditorReal)
    fresh_evidence_real = isinstance(deps.fresh_checker, FreshCheckerReal)
    combined = combine_batch_results(
        build,
        audit,
        fresh,
        axiom_evidence_real=axiom_evidence_real,
        fresh_evidence_real=fresh_evidence_real,
    )
    # In production, default to strict acceptance unless explicitly disabled.
    use_strict = os.environ.get("OBR_ACCEPTANCE_STRICT", "").strip().lower() in ("1", "true", "yes")
    if not use_strict and os.environ.get("OBR_ENV") == "production":
        use_strict = True
    if use_strict:
        combined = apply_acceptance_strict(combined, axiom_evidence_real, fresh_evidence_real)
    return combined
