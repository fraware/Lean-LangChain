"""Unit tests for path traversal safety."""

from pathlib import Path

import pytest

from obligation_runtime_lean_gateway.api.path_safety import resolve_under_root


def test_resolve_under_root_allows_valid_relative_path(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    path = resolve_under_root(root, "Mini/Basic.lean")
    assert path == root / "Mini" / "Basic.lean"
    assert path.resolve().is_relative_to(root.resolve())


def test_resolve_under_root_rejects_traversal(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    with pytest.raises(ValueError, match="escapes workspace"):
        resolve_under_root(root, "../other/file.lean")


def test_resolve_under_root_rejects_deep_traversal(tmp_path: Path) -> None:
    root = tmp_path / "workspace" / "project"
    root.mkdir(parents=True)
    with pytest.raises(ValueError, match="escapes workspace"):
        resolve_under_root(root, "sub/../../../other/file.lean")
