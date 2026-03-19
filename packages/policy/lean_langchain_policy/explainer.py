from __future__ import annotations

from lean_langchain_schemas.policy import PolicyDecision


def explain_policy_decision(decision: PolicyDecision) -> str:
    if not decision.reasons:
        return f"Decision: {decision.decision}. No additional reasons."
    joined = ", ".join(decision.reasons)
    return f"Decision: {decision.decision}. Reasons: {joined}."
