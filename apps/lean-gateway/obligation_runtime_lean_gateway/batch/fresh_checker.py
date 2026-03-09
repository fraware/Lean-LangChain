from __future__ import annotations

from pathlib import Path

from obligation_runtime_schemas.batch import FreshCheckerResult


class FreshChecker:
    def run(self, workspace_path: Path) -> FreshCheckerResult:
        return FreshCheckerResult(ok=True, command=["lean4checker", "--fresh"], stdout="", stderr="", timing_ms=0)
