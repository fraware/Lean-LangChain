"""Unit tests for PolicyEngine.evaluate()."""

from __future__ import annotations

from obligation_runtime_policy.engine import PolicyEngine
from obligation_runtime_policy.models import PolicyPack
from obligation_runtime_policy.patch_metadata import summarize_patch


def _strict_pack() -> PolicyPack:
    return PolicyPack(
        version="1.0",
        name="strict",
        description="Strict",
        allow_trust_compiler=False,
        require_human_if_imports_change=True,
        protected_paths=[],
    )


def test_policy_accepted_when_batch_ok_no_triggers() -> None:
    engine = PolicyEngine()
    pack = _strict_pack()
    result = engine.evaluate(
        obligation={},
        interactive_result={"diagnostics": [], "ok": True},
        batch_result={"ok": True, "trust_level": "clean", "build": {"ok": True}, "axiom_audit": {"blocked_reasons": []}, "fresh_checker": {"ok": True}},
        patch_metadata={"protected_paths_touched": False, "imports_changed": False},
        policy_pack=pack,
    )
    assert result.decision == "accepted"
    assert result.trust_level == "clean"


def test_policy_rejected_when_interactive_has_errors() -> None:
    engine = PolicyEngine()
    pack = _strict_pack()
    result = engine.evaluate(
        obligation={},
        interactive_result={"diagnostics": [{"severity": "error", "message": "type mismatch"}], "ok": False},
        batch_result=None,
        patch_metadata={},
        policy_pack=pack,
    )
    assert result.decision == "rejected"
    assert result.trust_level == "blocked"
    assert "interactive_errors_present" in result.reasons


def test_policy_rejected_when_batch_fails() -> None:
    engine = PolicyEngine()
    pack = _strict_pack()
    result = engine.evaluate(
        obligation={},
        interactive_result={"diagnostics": [], "ok": True},
        batch_result={"ok": False, "trust_level": "blocked", "build": {"ok": False}, "fresh_checker": {"ok": True}},
        patch_metadata={},
        policy_pack=pack,
    )
    assert result.decision == "rejected"
    assert result.trust_level == "blocked"
    assert "batch_verify_failed" in result.reasons
    assert "lake_build_failed" in result.reasons


def test_policy_needs_review_when_protected_paths_touched() -> None:
    engine = PolicyEngine()
    pack = PolicyPack(version="1", name="p", description="d", protected_paths=["Foo.lean"])
    result = engine.evaluate(
        obligation={},
        interactive_result={"diagnostics": [], "ok": True},
        batch_result={"ok": True, "trust_level": "clean", "build": {"ok": True}, "axiom_audit": {"blocked_reasons": []}, "fresh_checker": {"ok": True}},
        patch_metadata={"protected_paths_touched": True, "imports_changed": False},
        policy_pack=pack,
    )
    assert result.decision == "needs_review"
    assert "protected_path_touched" in result.reasons


def test_policy_needs_review_when_imports_changed() -> None:
    engine = PolicyEngine()
    pack = _strict_pack()
    result = engine.evaluate(
        obligation={},
        interactive_result={"diagnostics": [], "ok": True},
        batch_result={"ok": True, "trust_level": "clean", "build": {"ok": True}, "axiom_audit": {"blocked_reasons": []}, "fresh_checker": {"ok": True}},
        patch_metadata={"protected_paths_touched": False, "imports_changed": True},
        policy_pack=pack,
    )
    assert result.decision == "needs_review"
    assert "imports_changed_requires_review" in result.reasons


def test_policy_needs_review_when_summarize_patch_reports_protected_path_touched() -> None:
    """Patch metadata from summarize_patch with protected path touched => needs_review."""
    engine = PolicyEngine()
    pack = PolicyPack(version="1", name="p", description="d", protected_paths=["Foo.lean"])
    summary = summarize_patch(
        before={"Foo.lean": ""},
        after={"Foo.lean": "import X\n"},
        protected_paths=["Foo.lean"],
    )
    patch_meta = {
        "protected_paths_touched": summary["protected_paths_touched"],
        "imports_changed": summary["imports_changed"],
    }
    result = engine.evaluate(
        obligation={},
        interactive_result={"diagnostics": [], "ok": True},
        batch_result={"ok": True, "trust_level": "clean", "build": {"ok": True}, "axiom_audit": {"blocked_reasons": []}, "fresh_checker": {"ok": True}},
        patch_metadata=patch_meta,
        policy_pack=pack,
    )
    assert result.decision == "needs_review"
    assert "protected_path_touched" in result.reasons
