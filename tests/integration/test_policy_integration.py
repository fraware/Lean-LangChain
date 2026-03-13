"""Integration tests for PolicyEngine with canned evidence."""

from obligation_runtime_policy.engine import PolicyEngine
from obligation_runtime_policy.models import PolicyPack


def test_policy_engine_integration_accepted() -> None:
    """PolicyEngine.evaluate returns accepted when batch ok and no review triggers."""
    engine = PolicyEngine()
    pack = PolicyPack(version="1", name="strict", description="Strict", protected_paths=[])
    result = engine.evaluate(
        obligation={"kind": "patch_admissibility"},
        interactive_result={"ok": True, "diagnostics": []},
        batch_result={
            "ok": True,
            "trust_level": "clean",
            "build": {"ok": True},
            "axiom_audit": {"blocked_reasons": []},
            "fresh_checker": {"ok": True},
        },
        patch_metadata={"protected_paths_touched": False, "imports_changed": False},
        policy_pack=pack,
    )
    assert result.decision == "accepted"


def test_policy_engine_integration_rejected_on_batch_fail() -> None:
    """PolicyEngine.evaluate returns rejected when batch_result.ok is False."""
    engine = PolicyEngine()
    pack = PolicyPack(version="1", name="strict", description="Strict")
    result = engine.evaluate(
        obligation={},
        interactive_result={"ok": True, "diagnostics": []},
        batch_result={"ok": False, "trust_level": "blocked", "build": {"ok": False}, "fresh_checker": {"ok": True}},
        patch_metadata={},
        policy_pack=pack,
    )
    assert result.decision == "rejected"
    assert "lake_build_failed" in result.reasons
