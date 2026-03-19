"""V2 protocol evaluation: handoff_legality, reviewer_gated, lock_ownership_invariant.

All reason codes and decision literals are defined in .constants; use those
for consistency. Events are normalized from dict or model to dict with kind, actor, task.
"""

from __future__ import annotations

from typing import Any, cast

from lean_langchain_schemas.policy import PolicyDecision

from .constants import (
    DECISION_ACCEPTED,
    DECISION_BLOCKED,
    DECISION_REJECTED,
    REASON_ARTIFACT_NOT_ADMISSIBLE,
    REASON_DELEGATE_WITHOUT_PRIOR_CLAIM,
    REASON_EVIDENCE_INCOMPLETE,
    REASON_INVALID_STATE_TRANSITION,
    REASON_LOCK_CONFLICT,
    REASON_MISSING_APPROVAL_TOKEN,
    REASON_OWNER_MISMATCH,
    REASON_RELEASE_WITHOUT_LOCK,
    REASON_SIDE_EFFECT_UNAUTHORIZED,
    TRUST_BLOCKED,
    TRUST_CLEAN,
)
from .models import PolicyPack

try:
    from lean_langchain_protocol.models import ProtocolEvent
except ImportError:
    ProtocolEvent = None


def _event_to_dict(ev: object) -> dict[str, Any]:
    """Normalize event to dict with kind, actor, task; empty dict if invalid."""
    if isinstance(ev, dict):
        return cast(dict[str, Any], ev)
    if hasattr(ev, "model_dump"):
        return cast(dict[str, Any], ev.model_dump(mode="json"))
    return {}


def _validate_events(events: list[object]) -> list[dict[str, Any]]:
    """Normalize events to list of dicts with kind, actor, task (default {}). Skip non-dict/invalid."""
    out: list[dict[str, Any]] = []
    for ev in events:
        d = _event_to_dict(ev)
        if not isinstance(d, dict) or not d:
            continue
        actor = d.get("actor")
        task = d.get("task")
        if not isinstance(actor, dict):
            actor = {}
        if not isinstance(task, dict):
            task = {}
        out.append({**d, "actor": actor, "task": task})
    return out


def evaluate_handoff_legality(events: list[object], pack: PolicyPack) -> PolicyDecision:
    """Evaluate handoff_legality: if single_owner_handoff, delegate must be from same owner as claim."""
    if not pack.single_owner_handoff:
        return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
    normalized = _validate_events(events)
    claim_owner: str | None = None
    for ev_dict in normalized:
        kind = ev_dict.get("kind")
        actor = ev_dict.get("actor") or {}
        agent_id = actor.get("agent_id") if isinstance(actor, dict) else None
        if kind == "claim":
            claim_owner = agent_id
        elif kind == "delegate":
            if claim_owner is None:
                return PolicyDecision(
                    decision=DECISION_REJECTED,
                    trust_level=TRUST_BLOCKED,
                    reasons=[REASON_DELEGATE_WITHOUT_PRIOR_CLAIM],
                )
            if agent_id != claim_owner:
                return PolicyDecision(
                    decision=DECISION_REJECTED,
                    trust_level=TRUST_BLOCKED,
                    reasons=[REASON_OWNER_MISMATCH],
                )
    return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])


def evaluate_reviewer_gated(events: list[object], pack: PolicyPack) -> PolicyDecision:
    """Evaluate reviewer-gated execution: if pack requires it, events must contain an approve."""
    if not pack.reviewer_gated_execution:
        return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
    normalized = _validate_events(events)
    for ev_dict in normalized:
        if ev_dict.get("kind") == "approve":
            return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
    return PolicyDecision(
        decision=DECISION_BLOCKED,
        trust_level=TRUST_BLOCKED,
        reasons=[REASON_MISSING_APPROVAL_TOKEN],
    )


def evaluate_delegation_admissibility(events: list[object], pack: PolicyPack) -> PolicyDecision:
    """Delegate only after claim; same or allowed task. Same semantics as handoff for single-owner."""
    if not pack.delegation_admissibility:
        return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
    normalized = _validate_events(events)
    claim_task_id: str | None = None
    claim_owner: str | None = None
    for ev_dict in normalized:
        kind = ev_dict.get("kind")
        actor = ev_dict.get("actor") or {}
        task = ev_dict.get("task") or {}
        agent_id = actor.get("agent_id") if isinstance(actor, dict) else None
        task_id = task.get("task_id") if isinstance(task, dict) else None
        if kind == "claim":
            claim_owner = agent_id
            claim_task_id = task_id
        elif kind == "delegate":
            if claim_owner is None:
                return PolicyDecision(
                    decision=DECISION_REJECTED,
                    trust_level=TRUST_BLOCKED,
                    reasons=[REASON_DELEGATE_WITHOUT_PRIOR_CLAIM],
                )
            if agent_id != claim_owner:
                return PolicyDecision(
                    decision=DECISION_REJECTED,
                    trust_level=TRUST_BLOCKED,
                    reasons=[REASON_OWNER_MISMATCH],
                )
            if claim_task_id is not None and task_id is not None and task_id != claim_task_id:
                return PolicyDecision(
                    decision=DECISION_REJECTED,
                    trust_level=TRUST_BLOCKED,
                    reasons=[REASON_INVALID_STATE_TRANSITION],
                )
    return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])


def evaluate_state_transition_preservation(
    events: list[object], pack: PolicyPack
) -> PolicyDecision:
    """Allowed transitions: claim -> delegate -> approve/reject; execute/recover only after approve."""
    if not pack.state_transition_preservation:
        return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
    normalized = _validate_events(events)
    seen_approve = False
    for ev_dict in normalized:
        kind = ev_dict.get("kind")
        if kind in ("execute", "recover"):
            if not seen_approve:
                return PolicyDecision(
                    decision=DECISION_REJECTED,
                    trust_level=TRUST_BLOCKED,
                    reasons=[REASON_INVALID_STATE_TRANSITION],
                )
        elif kind == "approve":
            seen_approve = True
    return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])


def evaluate_artifact_admissibility(events: list[object], pack: PolicyPack) -> PolicyDecision:
    """Only approve/execute events may carry artifacts; others with non-empty artifact payload are rejected."""
    if not pack.artifact_admissibility:
        return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
    normalized = _validate_events(events)
    artifact_ok_kinds = {"approve", "execute"}
    for ev_dict in normalized:
        kind = ev_dict.get("kind")
        payload = ev_dict.get("payload") or {}
        has_artifact = bool(payload.get("artifacts") if isinstance(payload, dict) else False)
        if has_artifact and kind not in artifact_ok_kinds:
            return PolicyDecision(
                decision=DECISION_REJECTED,
                trust_level=TRUST_BLOCKED,
                reasons=[REASON_ARTIFACT_NOT_ADMISSIBLE],
            )
    return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])


def evaluate_side_effect_authorization(events: list[object], pack: PolicyPack) -> PolicyDecision:
    """Execute and recover only after an approve event."""
    if not pack.side_effect_authorization:
        return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
    normalized = _validate_events(events)
    seen_approve = False
    for ev_dict in normalized:
        kind = ev_dict.get("kind")
        if kind in ("execute", "recover"):
            if not seen_approve:
                return PolicyDecision(
                    decision=DECISION_REJECTED,
                    trust_level=TRUST_BLOCKED,
                    reasons=[REASON_SIDE_EFFECT_UNAUTHORIZED],
                )
        elif kind == "approve":
            seen_approve = True
    return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])


def evaluate_evidence_complete_execution_token(
    events: list[object], pack: PolicyPack
) -> PolicyDecision:
    """When pack requires it, events or payload must indicate evidence bundle complete (e.g. token or event kind)."""
    if not pack.evidence_complete_execution_token:
        return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
    normalized = _validate_events(events)
    for ev_dict in normalized:
        kind = ev_dict.get("kind")
        payload = ev_dict.get("payload") or {}
        if kind == "execute" and payload.get("evidence_complete") is True:
            return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
        if isinstance(payload, dict) and payload.get("evidence_complete") is True:
            return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
    return PolicyDecision(
        decision=DECISION_BLOCKED,
        trust_level=TRUST_BLOCKED,
        reasons=[REASON_EVIDENCE_INCOMPLETE],
    )


def evaluate_lock_ownership_invariant(events: list[object], pack: PolicyPack) -> PolicyDecision:
    """Evaluate lock ownership: only one holder; release must be by holder; no lock while held by another."""
    if not pack.lock_ownership_invariant:
        return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
    normalized = _validate_events(events)
    current_holder: str | None = None
    for ev_dict in normalized:
        kind = ev_dict.get("kind")
        actor = ev_dict.get("actor") or {}
        agent_id = actor.get("agent_id") if isinstance(actor, dict) else None
        if kind == "lock":
            if current_holder is not None and current_holder != agent_id:
                return PolicyDecision(
                    decision=DECISION_REJECTED,
                    trust_level=TRUST_BLOCKED,
                    reasons=[REASON_LOCK_CONFLICT],
                )
            current_holder = agent_id
        elif kind == "release":
            if current_holder is None:
                return PolicyDecision(
                    decision=DECISION_REJECTED,
                    trust_level=TRUST_BLOCKED,
                    reasons=[REASON_RELEASE_WITHOUT_LOCK],
                )
            if agent_id != current_holder:
                return PolicyDecision(
                    decision=DECISION_REJECTED,
                    trust_level=TRUST_BLOCKED,
                    reasons=[REASON_LOCK_CONFLICT],
                )
            current_holder = None
    return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])


def evaluate_protocol_obligation(
    obligation_class: str,
    events: list[object],
    pack: PolicyPack,
) -> PolicyDecision:
    """Dispatch by obligation class to the right evaluator. Events are normalized internally."""
    if obligation_class == "handoff_legality":
        return evaluate_handoff_legality(events, pack)
    if obligation_class == "reviewer_gated":
        return evaluate_reviewer_gated(events, pack)
    if obligation_class == "lock_ownership_invariant":
        return evaluate_lock_ownership_invariant(events, pack)
    if obligation_class == "delegation_admissibility":
        return evaluate_delegation_admissibility(events, pack)
    if obligation_class == "state_transition_preservation":
        return evaluate_state_transition_preservation(events, pack)
    if obligation_class == "artifact_admissibility":
        return evaluate_artifact_admissibility(events, pack)
    if obligation_class == "side_effect_authorization":
        return evaluate_side_effect_authorization(events, pack)
    if obligation_class == "evidence_complete_execution_token":
        return evaluate_evidence_complete_execution_token(events, pack)
    return PolicyDecision(decision=DECISION_ACCEPTED, trust_level=TRUST_CLEAN, reasons=[])
