#!/usr/bin/env python3
"""Run demo scenario 5 (multi-agent without reviewer token => blocked). Runs protocol evaluator with reviewer_gated pack and no approve event. Skips if policy pack not loadable."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from lean_langchain_policy.constants import (
            DECISION_BLOCKED,
            REASON_MISSING_APPROVAL_TOKEN,
        )
        from lean_langchain_policy.pack_loader import load_pack
        from lean_langchain_policy.protocol_evaluator import (
            evaluate_protocol_obligation,
        )
    except ImportError as e:
        print(f"Skipped: {e}", file=sys.stderr)
        return 0

    pack = load_pack("reviewer_gated_execution_v1")
    events = [
        {
            "kind": "claim",
            "event_id": "e1",
            "actor": {"agent_id": "alice", "role": "owner"},
            "task": {"task_id": "t1", "task_class": "patch"},
        },
        {
            "kind": "delegate",
            "event_id": "e2",
            "actor": {"agent_id": "alice", "role": "owner"},
            "task": {"task_id": "t1", "task_class": "patch"},
            "prior_event_ids": ["e1"],
        },
    ]
    result = evaluate_protocol_obligation("reviewer_gated", events, pack)
    if result.decision != DECISION_BLOCKED:
        print(
            f"Expected decision {DECISION_BLOCKED!r}, got {result.decision!r}",
            file=sys.stderr,
        )
        return 1
    if REASON_MISSING_APPROVAL_TOKEN not in result.reasons:
        print(
            f"Expected {REASON_MISSING_APPROVAL_TOKEN!r} in reasons, got {result.reasons!r}",
            file=sys.stderr,
        )
        return 1
    print("Scenario 5 passed: decision=blocked, reasons=", result.reasons)
    return 0


if __name__ == "__main__":
    sys.exit(main())
