"""Unit tests for policy pack loader."""

from obligation_runtime_policy.pack_loader import load_pack, list_packs


def test_load_pack_strict_patch_gate_v1() -> None:
    pack = load_pack("strict_patch_gate_v1")
    assert pack.name == "strict_patch_gate_v1"
    assert pack.allow_trust_compiler is False
    assert pack.require_human_if_imports_change is True


def test_list_packs_includes_expected() -> None:
    names = list_packs()
    assert "strict_patch_gate_v1" in names
    assert "protected_module_review_v1" in names
    assert "single_owner_handoff_v1" in names
    assert "reviewer_gated_execution_v1" in names


def test_load_single_owner_handoff_v1() -> None:
    pack = load_pack("single_owner_handoff_v1")
    assert pack.single_owner_handoff is True
    assert pack.name == "single_owner_handoff_v1"
