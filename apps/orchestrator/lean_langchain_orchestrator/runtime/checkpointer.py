from __future__ import annotations

import json
from pathlib import Path


class FileCheckpointer:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, thread_id: str, state: dict) -> None:
        (self.root / f"{thread_id}.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    def load(self, thread_id: str) -> dict | None:
        path = self.root / f"{thread_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
