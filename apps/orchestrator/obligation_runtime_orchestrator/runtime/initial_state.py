"""Canonical factory for initial ObligationRuntimeState. Use this instead of building state dicts by hand."""

from __future__ import annotations

from typing import Any

from obligation_runtime_orchestrator.runtime.state import ObligationRuntimeState


def make_initial_state(
    *,
    thread_id: str,
    obligation_id: str,
    obligation: dict,
    target_files: list[str],
    target_declarations: list[str] | None = None,
    current_patch: dict[str, str] | None = None,
    repo_path: str = "",
    session_id: str | None = None,
    policy_pack_name: str | None = None,
    protocol_events: list[dict] | None = None,
    **overrides: Any,
) -> ObligationRuntimeState:
    """Build a full ObligationRuntimeState with required keys and defaults.

    _repo_path is the internal repo path for the graph (CLI and callers set it when invoking).
    Pass any extra fields via overrides (e.g. for tests or case-specific state).
    """
    state: dict[str, Any] = {
        "thread_id": thread_id,
        "obligation_id": obligation_id,
        "obligation": obligation,
        "session_id": session_id,
        "environment_fingerprint": obligation.get("environment_fingerprint", {}),
        "target_files": target_files,
        "target_declarations": target_declarations or [],
        "current_patch": current_patch or {},
        "patch_history": [],
        "interactive_result": None,
        "goal_snapshots": [],
        "batch_result": None,
        "policy_decision": None,
        "trust_level": None,
        "approval_required": False,
        "approval_decision": None,
        "status": "initialized",
        "attempt_count": 0,
        "max_attempts": 3,
        "artifacts": [],
        "trace_events": [],
        "_repo_path": repo_path,
    }
    if policy_pack_name is not None:
        state["policy_pack_name"] = policy_pack_name
    if protocol_events is not None:
        state["protocol_events"] = protocol_events
    state.update(overrides)
    return state  # type: ignore[return-value]


def make_resume_state(
    *,
    thread_id: str,
    decision: str,
    **overrides: Any,
) -> ObligationRuntimeState:
    """Build state for resuming the graph after human approval (approve/reject).

    Use this from the orchestrator resume API and CLI so resume state is defined in one place.
    """
    if decision not in ("approved", "rejected"):
        raise ValueError(f"decision must be 'approved' or 'rejected', got {decision!r}")
    state: dict[str, Any] = {
        "thread_id": thread_id,
        "obligation_id": "",
        "session_id": None,
        "environment_fingerprint": {},
        "obligation": {},
        "target_files": [],
        "target_declarations": [],
        "current_patch": {},
        "patch_history": [],
        "interactive_result": None,
        "goal_snapshots": [],
        "batch_result": None,
        "policy_decision": None,
        "trust_level": None,
        "approval_required": True,
        "approval_decision": decision,
        "status": "awaiting_approval",
        "attempt_count": 0,
        "max_attempts": 3,
        "artifacts": [],
        "trace_events": [],
        "_repo_path": "",
    }
    state.update(overrides)
    return state  # type: ignore[return-value]
