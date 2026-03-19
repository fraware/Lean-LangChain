from __future__ import annotations

from typing import Literal

from obligation_runtime_schemas.batch import (
    BatchVerifyResult,
    BatchBuildResult,
    AxiomAuditResult,
    FreshCheckerResult,
)

REASON_STRICT_REQUIRES_REAL_AXIOM = "acceptance_strict_requires_real_axiom_audit"
REASON_STRICT_REQUIRES_REAL_FRESH = "acceptance_strict_requires_real_fresh_checker"


def apply_acceptance_strict(
    combined: BatchVerifyResult,
    axiom_evidence_real: bool,
    fresh_evidence_real: bool,
) -> BatchVerifyResult:
    """When acceptance strict is on, block if axiom or fresh evidence is not real."""
    reasons = []
    if not axiom_evidence_real:
        reasons.append(REASON_STRICT_REQUIRES_REAL_AXIOM)
    if not fresh_evidence_real:
        reasons.append(REASON_STRICT_REQUIRES_REAL_FRESH)
    if not reasons:
        return combined
    return combined.model_copy(
        update={
            "ok": False,
            "trust_level": "blocked",
            "reasons": [*combined.reasons, *reasons],
        }
    )


def combine_batch_results(
    build: BatchBuildResult,
    audit: AxiomAuditResult,
    fresh: FreshCheckerResult,
    *,
    axiom_evidence_real: bool = False,
    fresh_evidence_real: bool = False,
) -> BatchVerifyResult:
    ok = build.ok and audit.ok and fresh.ok and audit.trust_level != "blocked"
    reasons: list[str] = []
    if not build.ok:
        reasons.append("lake_build_failed")
    reasons.extend(audit.blocked_reasons)
    if not fresh.ok:
        reasons.append("fresh_checker_failed")
    trust_level: Literal["clean", "warning", "blocked"] = (
        "blocked" if audit.trust_level == "blocked" else audit.trust_level
    )
    return BatchVerifyResult(
        ok=ok,
        build=build,
        axiom_audit=audit,
        fresh_checker=fresh,
        trust_level=trust_level,
        reasons=reasons,
        axiom_evidence_real=axiom_evidence_real,
        fresh_evidence_real=fresh_evidence_real,
    )
