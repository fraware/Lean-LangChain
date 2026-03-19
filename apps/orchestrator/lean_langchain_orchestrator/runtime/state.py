from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


class InteractiveState(TypedDict, total=False):
    """Slice stored in ``interactive_result`` after interactive check."""

    ok: bool
    diagnostics: list[dict[str, Any]]
    goals: list[dict[str, Any]]


class BatchState(TypedDict, total=False):
    """Slice stored in ``batch_result`` after batch verify."""

    ok: bool
    trust_level: str
    build: dict[str, Any]
    axiom_audit: dict[str, Any]
    fresh_checker: dict[str, Any]


class PolicyResolvedRuleDict(TypedDict, total=False):
    rule_id: str
    source_pack: str
    matched: bool
    effect: str
    reason_code: str


class PolicyState(TypedDict, total=False):
    """Slice aligned with ``PolicyDecision`` (serialized to state)."""

    decision: str
    trust_level: str
    reasons: list[str]
    policy_pack_name: str
    policy_pack_version: str
    resolved_rules: list[PolicyResolvedRuleDict]


class ArtifactRecord(TypedDict, total=False):
    """Witness or other graph artifacts."""

    kind: str
    bundle: dict[str, Any]


class TraceEvent(TypedDict, total=False):
    event: str
    at: str
    data: dict[str, Any]


class ObligationRuntimeState(TypedDict):
    thread_id: str
    obligation_id: str
    environment_fingerprint: dict[str, Any]
    session_id: str | None
    obligation: dict[str, Any]
    target_files: list[str]
    target_declarations: list[str]
    current_patch: dict[str, str]
    patch_history: list[dict[str, str]]
    interactive_result: InteractiveState | None
    goal_snapshots: list[dict[str, Any]]
    batch_result: BatchState | None
    policy_decision: PolicyState | None
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
    artifacts: list[ArtifactRecord]
    trace_events: list[TraceEvent]
    protocol_events: NotRequired[list[dict[str, Any]]]
    policy_pack_name: NotRequired[str]
    _repo_path: NotRequired[str]
