from __future__ import annotations

from pathlib import Path
from uuid import uuid4

try:
    from fastapi import APIRouter
except Exception:  # pragma: no cover
    class APIRouter:
        def __init__(self): pass
        def post(self, *_args, **_kwargs):
            def deco(fn): return fn
            return deco

from obligation_runtime_lean_gateway.api import deps

router = APIRouter()


@router.post("/environments/open")
def open_environment(payload: dict) -> dict:
    repo_id = payload["repo_id"]
    repo_path = payload.get("repo_path")
    commit_sha = payload.get("commit_sha", "HEAD")
    repo_root = Path(repo_path) if repo_path else Path("tests/integration/fixtures/lean-mini")
    env = deps.fingerprints.build_from_repo(repo_root, repo_id=repo_id, commit_sha=commit_sha, repo_url=payload.get("repo_url"))
    snap = deps.snapshots.ensure_snapshot(env, repo_root)
    return {"fingerprint": env.model_dump(mode="json"), "fingerprint_id": env.fingerprint_id(), "snapshot_path": str(snap.base_path)}


@router.post("/sessions")
def create_session(payload: dict) -> dict:
    fingerprint_id = payload["fingerprint_id"]
    base_path = deps.snapshots.env_root / fingerprint_id / "base"
    snap_meta = deps.snapshots.env_root / fingerprint_id / "meta.json"
    if not base_path.exists():
        raise FileNotFoundError(f"Snapshot not found for {fingerprint_id}")
    from obligation_runtime_lean_gateway.environment.models import SnapshotRecord
    snapshot = SnapshotRecord(fingerprint_id=fingerprint_id, base_path=base_path, metadata_path=snap_meta)
    overlay = deps.overlays.create_overlay(snapshot)
    deps.interactive_api.open_session(session_id=overlay.session_id, fingerprint_id=fingerprint_id, workspace_path=overlay.overlay_path)
    return {"session_id": overlay.session_id, "fingerprint_id": fingerprint_id, "workspace_path": str(overlay.overlay_path)}
