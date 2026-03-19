from __future__ import annotations


def promote_trace_to_example(trace: dict) -> dict:
    return {
        "case_id": trace.get("obligation_id", "unknown"),
        "obligation": trace.get("obligation", {}),
        "expected": trace.get("expected", {}),
    }
