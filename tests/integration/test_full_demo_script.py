"""Integration tests for the full demo script (subprocess and settings).

Validates run_full_demo.py in different settings: --help exits zero,
gateway unreachable causes skip (exit 0), verbose flag does not crash.
No live Gateway; uses unreachable URL to trigger skip path.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _script_path() -> Path:
    root = Path(__file__).resolve().parent.parent.parent
    return root / "scripts" / "demos" / "run_full_demo.py"


def _run_script(
    args: list[str],
    env: dict[str, str] | None = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess:
    """Run the full demo script as subprocess; return CompletedProcess."""
    env = env or os.environ.copy()
    cmd = [sys.executable, str(_script_path())] + args
    cwd = str(Path(__file__).resolve().parent.parent.parent)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
        env=env,
    )


def test_full_demo_script_help_exits_zero() -> None:
    """Running the script with --help exits with code 0."""
    proc = _run_script(["--help"])
    assert proc.returncode == 0
    out = proc.stdout or ""
    assert "full" in out or "proof-preserving" in out or "6 steps" in out


def test_full_demo_script_gateway_unreachable_skips() -> None:
    """When Gateway URL is unreachable, script skips with exit 0 and message."""
    env = os.environ.copy()
    env["OBR_GATEWAY_URL"] = "http://127.0.0.1:39999"
    proc = _run_script([], env=env, timeout=20)
    assert proc.returncode == 0
    assert "Skipped" in (proc.stderr or "") or "Skipped" in (proc.stdout or "")


def test_full_demo_script_verbose_gateway_unreachable_skips() -> None:
    """With -v and unreachable Gateway, script still skips (no crash)."""
    env = os.environ.copy()
    env["OBR_GATEWAY_URL"] = "http://127.0.0.1:39998"
    proc = _run_script(["-v"], env=env, timeout=20)
    assert proc.returncode == 0
    assert "Skipped" in (proc.stderr or "") or "Skipped" in (proc.stdout or "")


def test_full_demo_script_ui_resume_flag_parsed() -> None:
    """Script accepts --ui-resume when gateway is down (skip before using it)."""
    env = os.environ.copy()
    env["OBR_GATEWAY_URL"] = "http://127.0.0.1:39997"
    proc = _run_script(["--ui-resume"], env=env, timeout=20)
    assert proc.returncode == 0
