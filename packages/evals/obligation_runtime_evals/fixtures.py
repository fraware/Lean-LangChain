"""Fixture families for patch and multi-agent golden cases."""

from __future__ import annotations

# Patch fixture families: each entry is a dict suitable for GoldenCase.model_validate(...)

FAMILY_good_patch = [
    {
        "case_id": "good_patch_1",
        "obligation_input": {
            "target_files": ["Main.lean"],
            "current_patch": {},
            "session_id": None,
        },
        "expected_decision": "accepted",
        "expected_trust_level": "clean",
        "expected_terminal_status": "accepted",
        "expected_reason_codes": [],
    },
]

FAMILY_sorry_case = [
    {
        "case_id": "sorry_case_1",
        "obligation_input": {"target_files": ["Main.lean"], "interactive_ok": False},
        "expected_decision": "rejected",
        "expected_trust_level": "warning",
        "expected_terminal_status": "rejected",
        "expected_reason_codes": [],
    },
]

FAMILY_trust_compiler_case = [
    {
        "case_id": "trust_compiler_1",
        "obligation_input": {"target_files": []},
        "expected_decision": "accepted",
        "expected_trust_level": "clean",
        "expected_terminal_status": "accepted",
        "expected_reason_codes": [],
    },
]

FAMILY_protected_path_case = [
    {
        "case_id": "protected_path_1",
        "obligation_input": {"protected_paths_touched": True},
        "expected_decision": "needs_review",
        "expected_trust_level": "warning",
        "expected_terminal_status": "awaiting_approval",
        "expected_reason_codes": ["protected_paths_touched"],
    },
]

FAMILY_interactive_pass_batch_fail = [
    {
        "case_id": "interactive_pass_batch_fail_1",
        "obligation_input": {"interactive_ok": True, "batch_ok": False},
        "expected_decision": "rejected",
        "expected_trust_level": "warning",
        "expected_terminal_status": "rejected",
        "expected_reason_codes": [],
    },
]

# Multi-agent fixture families (minimal until V2 runtime is wired)

FAMILY_handoff_good = [
    {
        "case_id": "handoff_good_1",
        "obligation_input": {"events": ["claim", "delegate"], "owner_match": True},
        "expected_decision": "accepted",
        "expected_trust_level": "clean",
        "expected_terminal_status": "accepted",
        "expected_reason_codes": [],
    },
]

FAMILY_handoff_bad_owner = [
    {
        "case_id": "handoff_bad_owner_1",
        "obligation_input": {"events": ["claim", "delegate"], "owner_match": False},
        "expected_decision": "rejected",
        "expected_trust_level": "blocked",
        "expected_terminal_status": "rejected",
        "expected_reason_codes": ["owner_mismatch"],
    },
]

FAMILY_missing_approval_token = [
    {
        "case_id": "missing_approval_1",
        "obligation_input": {"has_approval_token": False},
        "expected_decision": "blocked",
        "expected_trust_level": "blocked",
        "expected_terminal_status": "blocked",
        "expected_reason_codes": ["missing_approval_token"],
    },
]

FAMILY_lock_conflict = [
    {
        "case_id": "lock_conflict_1",
        "obligation_input": {"lock_held": True, "conflict": True},
        "expected_decision": "rejected",
        "expected_trust_level": "blocked",
        "expected_terminal_status": "rejected",
        "expected_reason_codes": ["lock_conflict"],
    },
]

PATCH_FAMILIES = [
    "good_patch",
    "sorry_case",
    "trust_compiler_case",
    "protected_path_case",
    "interactive_pass_batch_fail",
]

MULTI_AGENT_FAMILIES = [
    "handoff_good",
    "handoff_bad_owner",
    "missing_approval_token",
    "lock_conflict",
]
