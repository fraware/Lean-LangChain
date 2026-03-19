from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from uuid import uuid4


@dataclass(slots=True)
class Worker:
    worker_id: str
    fingerprint_id: str
    workspace_path: Path
    warm: bool = True
    last_used_at: float = 0.0

    def touch(self) -> None:
        self.last_used_at = monotonic()


class WorkerPool:
    def __init__(self) -> None:
        self._workers: dict[str, list[Worker]] = defaultdict(list)

    def acquire(self, fingerprint_id: str, workspace_path: Path) -> Worker:
        workers = self._workers[fingerprint_id]
        if workers:
            worker = workers[0]
            worker.touch()
            return worker
        worker = Worker(
            worker_id=f"wrk_{uuid4().hex}",
            fingerprint_id=fingerprint_id,
            workspace_path=workspace_path,
            last_used_at=monotonic(),
        )
        self._workers[fingerprint_id].append(worker)
        return worker
