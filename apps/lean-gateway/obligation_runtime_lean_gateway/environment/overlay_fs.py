from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4

from .models import OverlayRecord, SnapshotRecord


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
