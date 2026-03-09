from __future__ import annotations

from pathlib import Path

from obligation_runtime_schemas.batch import BatchBuildResult


class BuildRunner:
    """Run `lake build` in the overlay workspace.

    This starter scaffold returns a normalized placeholder result.
    Replace with a subprocess-based implementation in Phase 2.
    """

    def run(self, workspace_path: Path) -> BatchBuildResult:
        return BatchBuildResult(ok=True, command=["lake", "build"], stdout="", stderr="", timing_ms=0)
