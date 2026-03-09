from __future__ import annotations


def evaluate_decision(actual: dict, expected: dict) -> dict:
    return {
        "decision_match": actual.get("decision") == expected.get("decision"),
        "trust_match": actual.get("trust_level") == expected.get("trust_level"),
        "reasons_match": actual.get("reasons", []) == expected.get("reason_codes", []),
    }
