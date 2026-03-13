NODE_SPANS = [
    "obr.init_environment",
    "obr.retrieve_context",
    "obr.interactive_check",
    "obr.batch_verify",
    "obr.audit_trust",
    "obr.policy_review",
    "obr.interrupt_for_approval",
    "obr.finalize",
]

GATEWAY_SPANS = [
    "obr.gateway.interactive_check",
    "obr.gateway.batch_verify",
]

SPAN_BY_NODE: dict[str, str] = {
    "init_environment": "obr.init_environment",
    "retrieve_context": "obr.retrieve_context",
    "draft_candidate": "obr.retrieve_context",
    "interactive_check": "obr.interactive_check",
    "batch_verify": "obr.batch_verify",
    "audit_trust": "obr.audit_trust",
    "policy_review": "obr.policy_review",
    "interrupt_for_approval": "obr.interrupt_for_approval",
    "finalize": "obr.finalize",
    "resume_with_approval": "obr.finalize",
    "repair_from_diagnostics": "obr.interactive_check",
    "repair_from_goals": "obr.interactive_check",
}
