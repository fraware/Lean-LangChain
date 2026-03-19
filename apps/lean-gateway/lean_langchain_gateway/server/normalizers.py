from __future__ import annotations

from lean_langchain_schemas.diagnostics import Diagnostic, GoalSnapshot
from lean_langchain_schemas.interactive import InteractiveCheckResult


class InteractiveNormalizer:
    def diagnostics(self, raw: list[dict]) -> list[Diagnostic]:
        out: list[Diagnostic] = []
        for item in raw:
            out.append(
                Diagnostic(
                    severity=item.get("severity", "error"),
                    file=item.get("file", ""),
                    line=item.get("line", 1),
                    column=item.get("column", 1),
                    end_line=item.get("endLine"),
                    end_column=item.get("endColumn"),
                    code=item.get("code"),
                    message=item.get("message", ""),
                    source=item.get("source", "lean"),
                )
            )
        return out

    def goals(self, raw: list[dict]) -> list[GoalSnapshot]:
        out: list[GoalSnapshot] = []
        for item in raw:
            out.append(
                GoalSnapshot(
                    kind=item.get("kind", "plainGoal"),
                    text=item.get("text", ""),
                    file=item.get("file"),
                    line=item.get("line"),
                    column=item.get("column"),
                )
            )
        return out

    def result(
        self,
        *,
        ok: bool,
        diagnostics: list[dict],
        goals: list[dict],
        stdout: str = "",
        stderr: str = "",
        timing_ms: int = 0,
    ) -> InteractiveCheckResult:
        return InteractiveCheckResult(
            ok=ok,
            diagnostics=self.diagnostics(diagnostics),
            goals=self.goals(goals),
            stdout=stdout,
            stderr=stderr,
            timing_ms=timing_ms,
        )
