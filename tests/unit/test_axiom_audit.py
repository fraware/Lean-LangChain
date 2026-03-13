"""Unit tests for AxiomAuditor and AxiomAuditorReal."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from obligation_runtime_lean_gateway.batch.axiom_audit import (
    AxiomAuditor,
    AxiomAuditorReal,
    NON_REAL_AXIOM_AUDIT_REASON,
    _parse_axiom_stdout,
)


def test_axiom_auditor_test_double_returns_clean_with_non_real_reason() -> None:
    """AxiomAuditor used as test double (injected in conftest) returns ok=True, clean trust_level, and NON_REAL_AXIOM_AUDIT_REASON."""
    auditor = AxiomAuditor()
    result = auditor.run(Path("/ws"), ["Foo.bar"])
    assert result.ok is True
    assert result.trust_level == "clean"
    assert result.blocked_reasons == [NON_REAL_AXIOM_AUDIT_REASON]
    assert result.dependencies == []


def test_axiom_auditor_real_returns_clean_when_command_succeeds() -> None:
    """AxiomAuditorReal returns ok=True when subprocess returns 0."""
    with patch(
        "obligation_runtime_lean_gateway.batch.axiom_audit.subprocess.run"
    ) as run:
        run.return_value = type(
            "R", (), {"returncode": 0, "stdout": "", "stderr": ""}
        )()
        auditor = AxiomAuditorReal(timeout_seconds=5.0)
        result = auditor.run(Path("/ws"), [])
    assert result.ok is True
    assert result.trust_level == "clean"
    assert result.blocked_reasons == []


def test_axiom_auditor_real_returns_blocked_when_command_fails() -> None:
    """AxiomAuditorReal returns ok=False and blocked when subprocess fails."""
    with patch(
        "obligation_runtime_lean_gateway.batch.axiom_audit.subprocess.run"
    ) as run:
        run.return_value = type(
            "R", (), {"returncode": 1, "stdout": "", "stderr": "axiom violation"}
        )()
        auditor = AxiomAuditorReal(timeout_seconds=5.0)
        result = auditor.run(Path("/ws"), [])
    assert result.ok is False
    assert result.trust_level == "blocked"
    assert "axiom" in result.blocked_reasons[0].lower() or "violation" in result.blocked_reasons[0].lower()


def test_axiom_auditor_real_handles_timeout() -> None:
    """AxiomAuditorReal returns blocked on TimeoutExpired."""
    import subprocess
    with patch(
        "obligation_runtime_lean_gateway.batch.axiom_audit.subprocess.run"
    ) as run:
        run.side_effect = subprocess.TimeoutExpired(cmd=["lake", "build"], timeout=5)
        auditor = AxiomAuditorReal(timeout_seconds=5.0)
        result = auditor.run(Path("/ws"), [])
    assert result.ok is False
    assert result.trust_level == "blocked"
    assert "exceeded" in result.blocked_reasons[0].lower()


def test_parse_axiom_stdout() -> None:
    """_parse_axiom_stdout parses declaration: axiom1, axiom2 lines."""
    out = "Foo.bar: ax1, ax2\nBaz.qux: ax3"
    deps = _parse_axiom_stdout(out, [])
    assert len(deps) == 2
    assert deps[0].declaration == "Foo.bar"
    assert deps[0].axioms == ["ax1", "ax2"]
    assert deps[1].declaration == "Baz.qux"
    assert deps[1].axioms == ["ax3"]


def test_parse_axiom_stdout_single_axiom_and_empty_trailing() -> None:
    """_parse_axiom_stdout handles one declaration with one axiom and strips whitespace."""
    out = "declaration: axiom1, axiom2  \n  Other: only_one  "
    deps = _parse_axiom_stdout(out, [])
    assert len(deps) == 2
    assert deps[0].declaration == "declaration"
    assert deps[0].axioms == ["axiom1", "axiom2"]
    assert deps[1].declaration == "Other"
    assert deps[1].axioms == ["only_one"]


def test_parse_axiom_stdout_producer_format() -> None:
    """_parse_axiom_stdout parses output from axiom_list producer (e.g. Mini.add_zero_right: (none))."""
    out = "Mini.add_zero_right: (none)"
    deps = _parse_axiom_stdout(out, [])
    assert len(deps) == 1
    assert deps[0].declaration == "Mini.add_zero_right"
    assert deps[0].axioms == ["(none)"]


def test_parse_axiom_stdout_collect_axioms_style_multi_line() -> None:
    """_parse_axiom_stdout parses multi-line collectAxioms-style output (main-gate, no Lean)."""
    out = (
        "Mini.add_zero_right: (none)\n"
        "Mini.foo: Lean.Real.le, Lean.Nat.add_comm\n"
        "Some.other: ax1, ax2, ax3"
    )
    deps = _parse_axiom_stdout(out, [])
    assert len(deps) == 3
    assert deps[0].declaration == "Mini.add_zero_right"
    assert deps[0].axioms == ["(none)"]
    assert deps[1].declaration == "Mini.foo"
    assert deps[1].axioms == ["Lean.Real.le", "Lean.Nat.add_comm"]
    assert deps[2].declaration == "Some.other"
    assert deps[2].axioms == ["ax1", "ax2", "ax3"]
