from __future__ import annotations

import json
import os
import shutil
import stat
from pathlib import Path
from uuid import uuid4

from .models import OverlayRecord, SnapshotRecord


def _make_writable(path: Path) -> None:
    """Ensure the tree at path is writable (e.g. after copying from read-only base)."""
    path = Path(path)
    if not path.exists():
        return
    for root, _dirs, files in os.walk(path, topdown=False):
        root_path = Path(root)
        for name in files:
            p = root_path / name
            try:
                p.chmod(p.stat().st_mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            except OSError:
                pass
        for name in _dirs:
            p = root_path / name
            try:
                p.chmod(p.stat().st_mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            except OSError:
                pass
    try:
        path.chmod(path.stat().st_mode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    except OSError:
        pass


class OverlayFS:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.overlay_root = root / "overlays"
        self.overlay_root.mkdir(parents=True, exist_ok=True)

    def create_overlay(self, snapshot: SnapshotRecord) -> OverlayRecord:
        session_id = f"sess_{uuid4().hex}"
        overlay_root = self.overlay_root / session_id
        work_path = overlay_root / "work"
        metadata_path = overlay_root / "meta.json"

        shutil.copytree(snapshot.base_path, work_path)
        _make_writable(work_path)
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "session_id": session_id,
                    "fingerprint_id": snapshot.fingerprint_id,
                    "base_path": str(snapshot.base_path),
                },
                f,
                indent=2,
            )

        return OverlayRecord(
            session_id=session_id,
            fingerprint_id=snapshot.fingerprint_id,
            overlay_path=work_path,
            metadata_path=metadata_path,
        )
