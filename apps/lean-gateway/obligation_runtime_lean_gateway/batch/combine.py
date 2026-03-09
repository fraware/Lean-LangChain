from __future__ import annotations

from obligation_runtime_schemas.batch import BatchVerifyResult, BatchBuildResult, AxiomAuditResult, FreshCheckerResult


def combine_batch_results(build: BatchBuildResult, audit: AxiomAuditResult, fresh: FreshCheckerResult) -> BatchVerifyResult:
    ok = build.ok and audit.ok and fresh.ok and audit.trust_level != "blocked"
    reasons: list[str] = []
    if not build.ok:
        reasons.append("lake_build_failed")
    reasons.extend(audit.blocked_reasons)
    if not fresh.ok:
        reasons.append("fresh_checker_failed")
    trust_level = "blocked" if audit.trust_level == "blocked" else audit.trust_level
    return BatchVerifyResult(
        ok=ok,
        build=build,
        axiom_audit=audit,
        fresh_checker=fresh,
        trust_level=trust_level,
        reasons=reasons,
    )
