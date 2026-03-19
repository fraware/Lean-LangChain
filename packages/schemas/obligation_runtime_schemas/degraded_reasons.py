"""Machine-readable degraded / capability reason codes (gateway and orchestrator)."""

from __future__ import annotations

from typing import Literal

DegradedReasonCode = Literal[
    "lean_interactive_unconfigured",
    "axiom_audit_unconfigured",
    "fresh_checker_unconfigured",
    "review_store_memory",
    "checkpointer_memory",
    "checkpointer_unavailable",
    "langgraph_unavailable",
    "policy_pack_unresolved",
]

ALL_DEGRADED_REASON_CODES: tuple[str, ...] = (
    "lean_interactive_unconfigured",
    "axiom_audit_unconfigured",
    "fresh_checker_unconfigured",
    "review_store_memory",
    "checkpointer_memory",
    "checkpointer_unavailable",
    "langgraph_unavailable",
    "policy_pack_unresolved",
)
