from __future__ import annotations

from typing import Literal

from pydantic import Field

from obligation_runtime_schemas.common import StrictModel


class RuntimeNodeEvent(StrictModel):
    event_type: Literal["node_enter", "node_exit", "node_error"]
    span_name: str
    thread_id: str
    obligation_id: str
    node_name: str
    status: str
    timing_ms: int | None = None
    failure_class: str | None = None
    metadata: dict = Field(default_factory=dict)
