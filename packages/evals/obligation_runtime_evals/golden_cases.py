PATCH_CASES = [
    {
        "case_id": "patch_good_001",
        "expected": {"decision": "accepted", "trust_level": "clean", "reason_codes": []},
    },
    {
        "case_id": "patch_sorry_001",
        "expected": {
            "decision": "blocked",
            "trust_level": "blocked",
            "reason_codes": ["sorry_ax_detected"],
        },
    },
]

MULTI_AGENT_CASES = [
    {
        "case_id": "handoff_good_001",
        "expected": {"decision": "accepted", "trust_level": "clean", "reason_codes": []},
    },
    {
        "case_id": "handoff_missing_token_001",
        "expected": {
            "decision": "blocked",
            "trust_level": "blocked",
            "reason_codes": ["missing_approval_token"],
        },
    },
]
