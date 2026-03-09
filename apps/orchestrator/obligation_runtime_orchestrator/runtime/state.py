from __future__ import annotations

from typing import Literal, TypedDict


class ObligationRuntimeState(TypedDict):
    thread_id: str
    obligation_id: str
    environment_fingerprint: dict
    session_id: str | None
    obligation: dict
    target_files: list[str]
    target_declarations: list[str]
    current_patch: dict[str, str]
    patch_history: list[dict[str, str]]
    interactive_result: dict | None
    goal_snapshots: list[dict]
    batch_result: dict | None
    policy_decision: dict | None
    trust_level: Literal["clean", "warning", "blocked"] | None
    approval_required: bool
    approval_decision: Literal["pending", "approved", "rejected"] | None
    status: Literal[
        "initialized",
        "retrieving_context",
        "drafting",
        "checking_interactive",
        "repairing",
        "auditing",
        "awaiting_approval",
        "batch_verifying",
        "accepted",
        "rejected",
        "failed",
    ]
    attempt_count: int
    max_attempts: int
    artifacts: list[dict]
    trace_events: list[dict]
