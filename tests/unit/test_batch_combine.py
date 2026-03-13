"""Unit tests for combine_batch_results()."""

from __future__ import annotations

from obligation_runtime_lean_gateway.batch.combine import (
    REASON_STRICT_REQUIRES_REAL_AXIOM,
    REASON_STRICT_REQUIRES_REAL_FRESH,
    apply_acceptance_strict,
    combine_batch_results,
)
from obligation_runtime_schemas.batch import (
    AxiomAuditResult,
    BatchBuildResult,
    FreshCheckerResult,
)


def test_apply_acceptance_strict_blocks_when_evidence_not_real() -> None:
    """apply_acceptance_strict forces ok=False and trust_level=blocked when axiom or fresh not real."""
    combined = combine_batch_results(
        _build(True), _audit(True, "clean"), _fresh(True),
        axiom_evidence_real=False,
        fresh_evidence_real=False,
    )
    out = apply_acceptance_strict(combined, axiom_evidence_real=False, fresh_evidence_real=False)
    assert out.ok is False
    assert out.trust_level == "blocked"
    assert REASON_STRICT_REQUIRES_REAL_AXIOM in out.reasons
    assert REASON_STRICT_REQUIRES_REAL_FRESH in out.reasons


def test_apply_acceptance_strict_no_change_when_both_real() -> None:
    """apply_acceptance_strict returns unchanged result when both evidences are real."""
    combined = combine_batch_results(
        _build(True), _audit(True, "clean"), _fresh(True),
        axiom_evidence_real=True,
        fresh_evidence_real=True,
    )
    out = apply_acceptance_strict(combined, axiom_evidence_real=True, fresh_evidence_real=True)
    assert out.ok is combined.ok
    assert out.trust_level == combined.trust_level
    assert out.reasons == combined.reasons


def _build(ok: bool) -> BatchBuildResult:
    return BatchBuildResult(ok=ok, command=["lake", "build"], stdout="", stderr="", timing_ms=0)


def _audit(ok: bool, trust_level: str, blocked_reasons: list[str] | None = None) -> AxiomAuditResult:
    return AxiomAuditResult(ok=ok, trust_level=trust_level, blocked_reasons=blocked_reasons or [], dependencies=[])


def _fresh(ok: bool) -> FreshCheckerResult:
    return FreshCheckerResult(ok=ok, command=["lean4checker", "--fresh"], stdout="", stderr="", timing_ms=0)


def test_combine_all_ok_trust_clean() -> None:
    combined = combine_batch_results(_build(True), _audit(True, "clean"), _fresh(True))
    assert combined.ok is True
    assert combined.trust_level == "clean"
    assert combined.reasons == []


def test_combine_build_failed() -> None:
    combined = combine_batch_results(_build(False), _audit(True, "clean"), _fresh(True))
    assert combined.ok is False
    assert "lake_build_failed" in combined.reasons
    assert combined.trust_level == "clean"


def test_combine_audit_blocked() -> None:
    combined = combine_batch_results(
        _build(True),
        _audit(True, "blocked", blocked_reasons=["sorry_ax_detected"]),
        _fresh(True),
    )
    assert combined.ok is False
    assert combined.trust_level == "blocked"
    assert "sorry_ax_detected" in combined.reasons


def test_combine_fresh_checker_failed() -> None:
    combined = combine_batch_results(_build(True), _audit(True, "clean"), _fresh(False))
    assert combined.ok is False
    assert "fresh_checker_failed" in combined.reasons


def test_combine_evidence_flags_default_false() -> None:
    """Without passing evidence flags, axiom_evidence_real and fresh_evidence_real are False."""
    combined = combine_batch_results(_build(True), _audit(True, "clean"), _fresh(True))
    assert combined.axiom_evidence_real is False
    assert combined.fresh_evidence_real is False


def test_combine_evidence_flags_passed_through() -> None:
    """When axiom_evidence_real and fresh_evidence_real are True, they appear in the result."""
    combined = combine_batch_results(
        _build(True),
        _audit(True, "clean"),
        _fresh(True),
        axiom_evidence_real=True,
        fresh_evidence_real=True,
    )
    assert combined.axiom_evidence_real is True
    assert combined.fresh_evidence_real is True
