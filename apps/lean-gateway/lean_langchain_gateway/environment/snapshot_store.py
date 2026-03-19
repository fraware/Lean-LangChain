from __future__ import annotations

import json
import os
import shutil
import stat
from pathlib import Path

from lean_langchain_schemas.environment import EnvironmentFingerprint

from .models import SnapshotRecord


def _make_readonly(path: Path) -> None:
    """Make the tree at path read-only (no write bits). Dirs 0o555, files 0o444 on Unix.
    On Windows, sets read-only flag where supported; see platform docs for limitations."""
    path = Path(path)
    if not path.exists():
        return
    for root, dirs, files in os.walk(path, topdown=False):
        root_path = Path(root)
        for name in files:
            p = root_path / name
            try:
                mode = p.stat().st_mode
                p.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
            except OSError:
                pass
        for name in dirs:
            p = root_path / name
            try:
                mode = p.stat().st_mode
                p.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
            except OSError:
                pass
    try:
        mode = path.stat().st_mode
        path.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    except OSError:
        pass


class SnapshotStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.env_root = root / "environments"
        self.env_root.mkdir(parents=True, exist_ok=True)

    def ensure_snapshot(
        self, env: EnvironmentFingerprint, source_repo_root: Path
    ) -> SnapshotRecord:
        fid = env.fingerprint_id()
        snapshot_root = self.env_root / fid
        base_path = snapshot_root / "base"
        metadata_path = snapshot_root / "meta.json"

        if not base_path.exists():
            snapshot_root.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_repo_root, base_path)
            _make_readonly(base_path)
            with metadata_path.open("w", encoding="utf-8") as f:
                json.dump(env.model_dump(mode="json"), f, indent=2)

        return SnapshotRecord(fingerprint_id=fid, base_path=base_path, metadata_path=metadata_path)
