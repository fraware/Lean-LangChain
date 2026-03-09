from __future__ import annotations

from .events import RuntimeNodeEvent


class InMemoryTracer:
    def __init__(self) -> None:
        self.events: list[RuntimeNodeEvent] = []

    def emit(self, event: RuntimeNodeEvent) -> None:
        self.events.append(event)
