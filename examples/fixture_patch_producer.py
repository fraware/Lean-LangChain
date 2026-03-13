"""Fixture-based CandidateProducer: fixed patch from file or constant. No LLM."""

from __future__ import annotations

from pathlib import Path

from obligation_runtime_orchestrator.producer import ProducerContext


class FixturePatchProducer:
    """Producer that returns a patch from a file path or a constant. For tests and demos without API keys."""

    def __init__(
        self,
        patch_file: str | Path | None = None,
        constant_patch: dict[str, str] | None = None,
    ) -> None:
        if patch_file is not None and constant_patch is not None:
            raise ValueError("Provide either patch_file or constant_patch, not both.")
        self._patch_file = Path(patch_file) if patch_file else None
        self._constant_patch = constant_patch or {}

    def propose_patch(self, context: ProducerContext) -> dict[str, str]:
        if self._patch_file is not None and self._patch_file.exists():
            content = self._patch_file.read_text(encoding="utf-8")
            file_path = context.get("file_path") or "Main.lean"
            return {file_path: content}
        return dict(self._constant_patch)
