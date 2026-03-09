from __future__ import annotations

from typing import Literal

from .common import StrictModel


class Diagnostic(StrictModel):
    severity: Literal["error", "warning", "information", "hint"]
    file: str
    line: int
    column: int
    end_line: int | None = None
    end_column: int | None = None
    code: str | None = None
    message: str
    source: str = "lean"


class GoalSnapshot(StrictModel):
    kind: Literal["plainGoal", "plainTermGoal"]
    text: str
    file: str | None = None
    line: int | None = None
    column: int | None = None
