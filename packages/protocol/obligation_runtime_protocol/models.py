from __future__ import annotations

from typing import Literal

from pydantic import Field

from obligation_runtime_schemas.common import StrictModel


class AgentRef(StrictModel):
    agent_id: str
    role: str


class TaskRef(StrictModel):
    task_id: str
    task_class: str


class ProtocolEvent(StrictModel):
    event_id: str
    kind: Literal["claim", "delegate", "approve", "reject", "lock", "release", "execute", "recover"]
    actor: AgentRef
    task: TaskRef
    payload: dict = Field(default_factory=dict)
    prior_event_ids: list[str] = Field(default_factory=list)
