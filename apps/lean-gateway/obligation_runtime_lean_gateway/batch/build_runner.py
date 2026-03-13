"""Run `lake build` in the overlay workspace. Uses LeanRunner (local or container)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from obligation_runtime_schemas.batch import BatchBuildResult

from obligation_runtime_lean_gateway.server.runner import get_runner
from obligation_runtime_lean_gateway.server.worker_runner import DEFAULT_WALL_CLOCK_SECONDS

if TYPE_CHECKING:
    from obligation_runtime_lean_gateway.server.runner import LeanRunner


def _build_timeout_seconds() -> float:
    """Timeout for lake build; use OBR_BUILD_TIMEOUT env if set (e.g. for tests)."""
    env = os.environ.get("OBR_BUILD_TIMEOUT")
    if env is not None:
        try:
            return float(env)
        except ValueError:
            pass
    return DEFAULT_WALL_CLOCK_SECONDS


class BuildRunner:
    """Run `lake build` in the overlay workspace.

    Uses an optional LeanRunner (default from get_runner(): local or container).
    On timeout or missing binary returns ok=False.
    """

    def __init__(
        self,
        timeout_seconds: float | None = None,
        runner: LeanRunner | None = None,
    ) -> None:
        self._timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else _build_timeout_seconds()
        )
        self._runner = runner if runner is not None else get_runner("batch")

    def run(self, workspace_path: Path) -> BatchBuildResult:
        command = ["lake", "build"]
        workspace_path = Path(workspace_path)
        stdout, stderr, returncode, timing_ms = self._runner.run(
            workspace_path,
            command,
            self._timeout_seconds,
        )
        ok = returncode == 0
        if not ok and returncode == -1:
            # Timeout or OSError from runner
            pass
        return BatchBuildResult(
            ok=ok,
            command=command,
            stdout=stdout,
            stderr=stderr,
            timing_ms=timing_ms,
        )
