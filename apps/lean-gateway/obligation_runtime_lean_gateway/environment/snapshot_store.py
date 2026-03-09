from __future__ import annotations

import json
import shutil
from pathlib import Path

from obligation_runtime_schemas.environment import EnvironmentFingerprint

from .models import SnapshotRecord


class SnapshotStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.env_root = root / "environments"
        self.env_root.mkdir(parents=True, exist_ok=True)

    def ensure_snapshot(self, env: EnvironmentFingerprint, source_repo_root: Path) -> SnapshotRecord:
        fid = env.fingerprint_id()
        snapshot_root = self.env_root / fid
        base_path = snapshot_root / "base"
        metadata_path = snapshot_root / "meta.json"

        if not base_path.exists():
            snapshot_root.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_repo_root, base_path)
            with metadata_path.open("w", encoding="utf-8") as f:
                json.dump(env.model_dump(mode="json"), f, indent=2)

        return SnapshotRecord(fingerprint_id=fid, base_path=base_path, metadata_path=metadata_path)
