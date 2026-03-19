from __future__ import annotations

from pydantic import Field

from .common import VersionedRecord
from .diagnostics import Diagnostic, GoalSnapshot


class InteractiveCheckResult(VersionedRecord):
    ok: bool
    phase: str = "interactive"
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    goals: list[GoalSnapshot] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    timing_ms: int = 0
