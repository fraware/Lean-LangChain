"""Routing functions for the patch-admissibility graph. Stable service boundary: state -> next node name."""

from __future__ import annotations

from lean_langchain_orchestrator.runtime.state import ObligationRuntimeState


def route_after_interactive(state: ObligationRuntimeState) -> str:
    """From interactive_check: batch_verify, repair_from_diagnostics, or repair_from_goals."""
    ir = state.get("interactive_result")
    if not ir:
        return "batch_verify"
    if not ir.get("ok"):
        return "repair_from_diagnostics"
    if ir.get("goals") and any(g.get("text") for g in ir.get("goals", [])):
        return "repair_from_goals"
    return "batch_verify"


def route_after_policy(state: ObligationRuntimeState) -> str:
    """From policy_review: finalize, interrupt_for_approval, or __end__."""
    pd = state.get("policy_decision")
    if not pd:
        return "finalize"
    decision = pd.get("decision", "failed")
    if decision == "accepted":
        return "finalize"
    if decision == "needs_review":
        return "interrupt_for_approval"
    return "__end__"


def route_start(state: ObligationRuntimeState) -> str:
    """From START: resume_with_approval if approval_decision set, else init_environment."""
    if state.get("approval_required") and state.get("approval_decision") in (
        "approved",
        "rejected",
    ):
        return "resume_with_approval"
    return "init_environment"


def route_after_resume(state: ObligationRuntimeState) -> str:
    """From resume_with_approval: finalize if approved, else __end__."""
    if state.get("approval_decision") == "approved":
        return "finalize"
    return "__end__"
