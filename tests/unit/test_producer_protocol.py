"""Unit tests for CandidateProducer protocol and context_from_state."""

from __future__ import annotations

from lean_langchain_orchestrator.producer import (
    CandidateProducer,
    ProducerContext,
    context_from_state,
)


class TrivialProducer:
    """Minimal producer that returns a constant patch."""

    def propose_patch(self, context: ProducerContext) -> dict[str, str]:
        return {"Main.lean": "def x := 1\n"}


def test_context_from_state_shape() -> None:
    """context_from_state builds ProducerContext with target_files, file_path, diagnostics, goals, session_id."""
    state = {
        "target_files": ["Mini/Basic.lean", "Other.lean"],
        "session_id": "sess-1",
        "interactive_result": {
            "diagnostics": [{"message": "err"}],
            "goals": [{"text": "goal 1"}],
        },
    }
    ctx = context_from_state(state)
    assert ctx["target_files"] == ["Mini/Basic.lean", "Other.lean"]
    assert ctx["file_path"] == "Mini/Basic.lean"
    assert ctx["session_id"] == "sess-1"
    assert ctx["diagnostics"] == [{"message": "err"}]
    assert ctx["goals"] == [{"text": "goal 1"}]


def test_context_from_state_empty() -> None:
    """context_from_state with minimal state has file_path None when no target_files."""
    state = {"target_files": [], "interactive_result": None}
    ctx = context_from_state(state)
    assert ctx["target_files"] == []
    assert ctx.get("file_path") is None


def test_trivial_producer_implements_protocol() -> None:
    """A trivial producer returns a patch dict; protocol is satisfied."""
    producer: CandidateProducer = TrivialProducer()
    context: ProducerContext = {"target_files": ["Main.lean"], "file_path": "Main.lean"}
    patch = producer.propose_patch(context)
    assert isinstance(patch, dict)
    assert patch.get("Main.lean") == "def x := 1\n"
