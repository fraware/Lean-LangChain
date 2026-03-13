"""Provider-agnostic candidate producer interface for optional patch generation.

The core runtime only accepts current_patch from the caller. This module
defines a protocol so that demo mode or external adapters can plug in a
producer (e.g. LLM-backed) without the graph depending on generation.
Generation stays outside the trust core.
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict


class ProducerContext(TypedDict, total=False):
    """Context passed to propose_patch. Minimal fields for first attempt and repair loops."""

    target_files: list[str]
    file_path: str | None
    diagnostics: list[dict[str, Any]] | None
    goals: list[dict[str, Any]] | None
    session_id: str | None


class CandidateProducer(Protocol):
    """Protocol for a candidate patch producer. Implement in examples/ or adapters."""

    def propose_patch(self, context: ProducerContext) -> dict[str, str]:
        """Propose a patch: path -> content (workspace-relative)."""
        ...


def context_from_state(state: dict[str, Any]) -> ProducerContext:
    """Build ProducerContext from graph state for use by a producer."""
    target_files = state.get("target_files") or []
    file_path = target_files[0] if target_files else None
    inter = state.get("interactive_result") or {}
    return ProducerContext(
        target_files=target_files,
        file_path=file_path,
        diagnostics=inter.get("diagnostics"),
        goals=inter.get("goals"),
        session_id=state.get("session_id"),
    )
