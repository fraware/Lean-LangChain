from __future__ import annotations

from pathlib import Path

try:
    from fastapi import APIRouter
except Exception:  # pragma: no cover
    from lean_langchain_gateway.api.fastapi_shim import APIRouter  # type: ignore[assignment]

from lean_langchain_schemas.api_paths import PATH_ENVIRONMENTS_OPEN, PATH_SESSIONS
from lean_langchain_schemas.gateway_api import (
    CreateSessionRequest,
    CreateSessionResponse,
    OpenEnvironmentRequest,
    OpenEnvironmentResponse,
)

from lean_langchain_gateway.api import deps

router = APIRouter()


@router.post(PATH_ENVIRONMENTS_OPEN, response_model=OpenEnvironmentResponse)
def open_environment(payload: OpenEnvironmentRequest) -> OpenEnvironmentResponse:
    repo_root = (
        Path(payload.repo_path)
        if payload.repo_path
        else Path("tests/integration/fixtures/lean-mini")
    )
    commit_sha = payload.commit_sha or "HEAD"
    env = deps.fingerprints.build_from_repo(
        repo_root,
        repo_id=payload.repo_id,
        commit_sha=commit_sha,
        repo_url=payload.repo_url,
    )
    snap = deps.snapshots.ensure_snapshot(env, repo_root)
    return OpenEnvironmentResponse(
        fingerprint=env,
        fingerprint_id=env.fingerprint_id(),
        snapshot_path=str(snap.base_path),
    )


@router.post(PATH_SESSIONS, response_model=CreateSessionResponse)
def create_session(payload: CreateSessionRequest) -> CreateSessionResponse:
    fingerprint_id = payload.fingerprint_id
    base_path = deps.snapshots.env_root / fingerprint_id / "base"
    snap_meta = deps.snapshots.env_root / fingerprint_id / "meta.json"
    if not base_path.exists():
        raise FileNotFoundError(f"Snapshot not found for {fingerprint_id}")
    from lean_langchain_gateway.environment.models import SnapshotRecord

    snapshot = SnapshotRecord(
        fingerprint_id=fingerprint_id, base_path=base_path, metadata_path=snap_meta
    )
    overlay = deps.overlays.create_overlay(snapshot)
    deps.interactive_api.open_session(
        session_id=overlay.session_id,
        fingerprint_id=fingerprint_id,
        workspace_path=overlay.overlay_path,
    )
    return CreateSessionResponse(
        session_id=overlay.session_id,
        fingerprint_id=fingerprint_id,
        workspace_path=str(overlay.overlay_path),
    )
