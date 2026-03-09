from __future__ import annotations


def run_experiment(name: str, cases: list[dict]) -> dict:
    return {"experiment": name, "case_count": len(cases), "status": "stub"}
