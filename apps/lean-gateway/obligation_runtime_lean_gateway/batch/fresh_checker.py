"""Fresh checker for acceptance lane. Production uses FreshCheckerReal (OBR_USE_REAL_FRESH_CHECKER); FreshChecker is for test double injection only."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

from obligation_runtime_schemas.batch import FreshCheckerResult

from obligation_runtime_lean_gateway.server.worker_runner import DEFAULT_WALL_CLOCK_SECONDS

if TYPE_CHECKING:
    from obligation_runtime_lean_gateway.server.runner import LeanRunner


def _fresh_timeout_seconds() -> float:
    """Timeout for fresh check subprocess; OBR_FRESH_CHECK_TIMEOUT env for tests."""
    env = os.environ.get("OBR_FRESH_CHECK_TIMEOUT")
    if env is not None:
        try:
            return float(env)
        except ValueError:
            pass
    return min(120.0, DEFAULT_WALL_CLOCK_SECONDS)


class FreshChecker:
    """Test double only: returns deterministic ok. Production uses FreshCheckerReal; inject this only in tests."""

    def run(self, workspace_path: Path) -> FreshCheckerResult:
        return FreshCheckerResult(
            ok=True,
            command=["lean4checker", "--fresh"],
            stdout="",
            stderr="",
            timing_ms=0,
        )


class FreshCheckerReal:
    """Real fresh check: runs lean4checker (or OBR_FRESH_CHECK_CMD) in the workspace.

    Requires lean4checker (or the command in OBR_FRESH_CHECK_CMD) to be in PATH; CI does not
    install it. Optional LeanRunner for container execution. On timeout or OSError returns ok=False.
    See docs/running.md for OBR_USE_REAL_FRESH_CHECKER and OBR_FRESH_CHECK_CMD.
    """

    def __init__(
        self,
        timeout_seconds: float | None = None,
        runner: LeanRunner | None = None,
    ) -> None:
        self._timeout = (
            timeout_seconds if timeout_seconds is not None else _fresh_timeout_seconds()
        )
        cmd_env = os.environ.get("OBR_FRESH_CHECK_CMD")
        self._cmd = cmd_env.split() if cmd_env else ["lean4checker", "--fresh"]
        self._runner = runner

    def run(self, workspace_path: Path) -> FreshCheckerResult:
        workspace_path = Path(workspace_path)
        if self._runner is not None:
            stdout, stderr, returncode, timing_ms = self._runner.run(
                workspace_path, self._cmd, self._timeout
            )
            return FreshCheckerResult(
                ok=returncode == 0,
                command=self._cmd,
                stdout=stdout,
                stderr=stderr,
                timing_ms=timing_ms,
            )
        start = time.perf_counter()
        try:
            result = subprocess.run(
                self._cmd,
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return FreshCheckerResult(
                ok=result.returncode == 0,
                command=self._cmd,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                timing_ms=elapsed_ms,
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = int(self._timeout * 1000)
            return FreshCheckerResult(
                ok=False,
                command=self._cmd,
                stdout="",
                stderr=f"Fresh check exceeded {self._timeout}s",
                timing_ms=elapsed_ms,
            )
        except OSError as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return FreshCheckerResult(
                ok=False,
                command=self._cmd,
                stdout="",
                stderr=str(e),
                timing_ms=elapsed_ms,
            )
