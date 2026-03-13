"""Worker isolation: overlay receives patch; base snapshot unchanged (covered in test_gateway_api)."""

from pathlib import Path


def test_worker_isolation_overlay_base_unchanged(gateway_client) -> None:
    """Open env, create session, apply patch; overlay has new content, base snapshot unchanged."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    fid = open_resp.json()["fingerprint_id"]
    session_resp = client.post("/v1/sessions", json={"fingerprint_id": fid})
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    workspace_path = Path(session_resp.json()["workspace_path"])
    patched = "-- overlay isolation test\n"
    apply_resp = client.post(
        f"/v1/sessions/{session_id}/apply-patch",
        json={"files": {"Mini/Basic.lean": patched}},
    )
    assert apply_resp.status_code == 200
    overlay_file = workspace_path / "Mini" / "Basic.lean"
    assert overlay_file.exists()
    assert patched in overlay_file.read_text(encoding="utf-8")
    base_path = Path(".var") / "environments" / fid / "base" / "Mini" / "Basic.lean"
    if base_path.exists():
        assert patched not in base_path.read_text(encoding="utf-8")
