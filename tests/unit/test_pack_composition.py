"""Policy pack composition (extends/import) and path_rules."""

from __future__ import annotations

from pathlib import Path

import pytest

from lean_langchain_policy.engine import PolicyEngine
from lean_langchain_policy.pack_loader import clear_pack_resolution_cache, load_pack
from lean_langchain_policy.models import PathRule, PolicyPack


@pytest.fixture(autouse=True)
def _clear_pack_cache() -> None:
    clear_pack_resolution_cache()
    yield
    clear_pack_resolution_cache()


def test_extends_merges_base_flags() -> None:
    p = load_pack("loose_imports_v1")
    assert p.name == "loose_imports_v1"
    assert p.require_human_if_imports_change is False
    assert p.block_sorry_ax is True


def test_path_rules_trigger_review() -> None:
    engine = PolicyEngine()
    pack = PolicyPack(
        version="1",
        name="t",
        description="t",
        path_rules=[PathRule(glob="Core/*.lean", require_human=True, reason_code="core_touch")],
    )
    d = engine.evaluate(
        obligation={},
        interactive_result=None,
        batch_result={"ok": True, "trust_level": "clean", "axiom_audit": {"blocked_reasons": []}},
        patch_metadata={"changed_files": ["Core/Foo.lean"]},
        policy_pack=pack,
    )
    assert d.decision == "needs_review"
    assert "core_touch" in d.reasons


def test_import_list_later_pack_wins_on_scalar_conflict(tmp_path: Path) -> None:
    """Later `import` entry overwrites earlier merged keys (shallow merge)."""
    a = tmp_path / "a.yaml"
    a.write_text(
        """
version: "1"
name: pack_a
description: a
block_sorry_ax: false
require_human_if_imports_change: true
""",
        encoding="utf-8",
    )
    b = tmp_path / "b.yaml"
    b.write_text(
        """
version: "1"
name: pack_b
description: b
block_sorry_ax: true
""",
        encoding="utf-8",
    )
    child = tmp_path / "child.yaml"
    child.write_text(
        f"""
import:
  - {a.as_posix()}
  - {b.as_posix()}
version: "0.1.0"
name: child_order
description: child
require_human_if_imports_change: false
""",
        encoding="utf-8",
    )
    p = load_pack(str(child))
    assert p.name == "child_order"
    assert p.block_sorry_ax is True
    assert p.require_human_if_imports_change is False


def test_error_on_import_scalar_override_conflicting_imports(tmp_path: Path) -> None:
    """Strict policy: two imports disagreeing on a scalar flag raises."""
    a = tmp_path / "sa.yaml"
    a.write_text(
        """
version: "1"
name: sa
description: a
require_human_if_imports_change: true
""",
        encoding="utf-8",
    )
    b = tmp_path / "sb.yaml"
    b.write_text(
        """
version: "1"
name: sb
description: b
require_human_if_imports_change: false
""",
        encoding="utf-8",
    )
    child = tmp_path / "strict_child.yaml"
    child.write_text(
        f"""
composition_conflict_policy: error_on_import_scalar_override
import:
  - {a.as_posix()}
  - {b.as_posix()}
version: "0.1.0"
name: strict_child
description: child
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="error_on_import_scalar_override"):
        load_pack(str(child))


def test_custom_pack_with_import(tmp_path: Path) -> None:
    child = tmp_path / "child.yaml"
    child.write_text(
        """
import:
  - strict_patch_gate_v1
version: "0.1.0"
name: child_import
description: child
require_human_if_imports_change: false
""",
        encoding="utf-8",
    )
    p = load_pack(str(child))
    assert p.name == "child_import"
    assert p.require_human_if_imports_change is False
