from __future__ import annotations


def build_dataset_case(case_id: str, obligation: dict, expected: dict) -> dict:
    return {"case_id": case_id, "obligation": obligation, "expected": expected}
