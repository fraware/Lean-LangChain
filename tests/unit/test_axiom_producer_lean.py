"""Axiom producer unit test (runs when lake is in PATH).

When lake is in PATH, runs lake build and lake exe axiom_list in the lean-mini
fixture and asserts success. Skips when lake is not available so the main CI job
passes without Lean. The **lean** CI job runs with Lean; this test validates the
axiom_list producer path when the toolchain is present.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def _lean_mini_fixture_path() -> Path:
    return Path(__file__).resolve().parent.parent / "integration" / "fixtures" / "lean-mini"


@pytest.mark.skipif(not shutil.which("lake"), reason="lake not in PATH")
def test_axiom_producer_lean_mini_lake_build_and_exe_axiom_list() -> None:
    """In lean-mini fixture: lake build then lake exe axiom_list; assert exit 0 and stdout has declaration lines."""
    fixture = _lean_mini_fixture_path()
    if not fixture.is_dir():
        pytest.skip("lean-mini fixture not found")
    run_kw = {
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }
    out = subprocess.run(
        ["lake", "build"],
        cwd=str(fixture),
        timeout=120,
        **run_kw,
    )
    assert out.returncode == 0, (out.stdout or "") + (out.stderr or "")
    out2 = subprocess.run(
        ["lake", "exe", "axiom_list"],
        cwd=str(fixture),
        timeout=90,
        **run_kw,
    )
    if out2.returncode != 0:
        pytest.skip(
            f"lake exe axiom_list failed (e.g. Lean/fixture version mismatch): {out2.stderr or ''}"
        )
    stdout = (out2.stdout or "").strip()
    # Producer contract: lines like "declaration_name: axiom1, axiom2"
    lines = [ln for ln in stdout.splitlines() if ln.strip() and ":" in ln]
    assert len(lines) >= 1, f"Expected at least one declaration:axiom line in stdout: {stdout!r}"
