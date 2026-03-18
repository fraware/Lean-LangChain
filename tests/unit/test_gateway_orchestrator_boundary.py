"""Enforce gateway-orchestrator boundary: gateway must not import orchestrator runtime.

Prevents regressions where lean-gateway would depend on obligation_runtime_orchestrator
(e.g. for resume flow). Resume is delegated via OBR_ORCHESTRATOR_URL HTTP calls.
"""

from __future__ import annotations

import ast
from pathlib import Path


def _gateway_api_source_paths() -> list[Path]:
    """Return paths of gateway API Python modules that must not import orchestrator."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    gateway_api = repo_root / "apps" / "lean-gateway" / "obligation_runtime_lean_gateway" / "api"
    if not gateway_api.is_dir():
        return []
    return list(gateway_api.glob("*.py"))


def test_gateway_api_does_not_import_orchestrator_runtime() -> None:
    """Gateway API modules must not import obligation_runtime_orchestrator."""
    forbidden = "obligation_runtime_orchestrator"
    for path in _gateway_api_source_paths():
        if path.name.startswith("__"):
            continue
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == forbidden or alias.name.startswith(forbidden + "."):
                        repo_root = Path(__file__).resolve().parent.parent.parent
                        raise AssertionError(
                            f"{path.relative_to(repo_root)} must not import {forbidden}; "
                            "use OBR_ORCHESTRATOR_URL HTTP boundary instead."
                        )
            if isinstance(node, ast.ImportFrom):
                if node.module and (node.module == forbidden or node.module.startswith(forbidden + ".")):
                    repo_root = Path(__file__).resolve().parent.parent.parent
                    raise AssertionError(
                        f"{path.relative_to(repo_root)} must not import from {forbidden}; "
                        "use OBR_ORCHESTRATOR_URL HTTP boundary instead."
                    )
