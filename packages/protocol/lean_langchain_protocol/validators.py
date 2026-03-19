from __future__ import annotations

from .models import ProtocolEvent


def validate_single_owner(events: list[ProtocolEvent]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    owners: dict[str, str] = {}
    for event in events:
        if event.kind == "delegate":
            new_owner = event.payload.get("to_agent_id")
            task_id = event.task.task_id
            if task_id in owners and owners[task_id] != event.actor.agent_id:
                reasons.append("multiple_active_owners")
            owners[task_id] = str(new_owner)
    return (len(reasons) == 0, reasons)
