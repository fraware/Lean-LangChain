import os
from pathlib import Path

import pytest


def test_health_returns_ok(gateway_client) -> None:
    """GET /health returns 200, status ok, and capability snapshot."""
    client = gateway_client
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "degraded" in body
    assert body["capabilities"]["lean_interactive"] == "test_injected"
    assert body["capabilities"]["review_store"] in ("memory", "postgres")


def test_ready_returns_ready(gateway_client) -> None:
    """GET /ready returns 200 and status ready plus capability block."""
    client = gateway_client
    r = client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert "capabilities" in body
    assert "degraded" in body


def test_metrics_404_when_disabled(gateway_client) -> None:
    """GET /metrics returns 404 when OBR_METRICS_ENABLED is not set."""
    client = gateway_client
    r = client.get("/metrics")
    assert r.status_code == 404


@pytest.mark.skipif(
    not os.environ.get("OBR_METRICS_ENABLED"),
    reason="Set OBR_METRICS_ENABLED=1 and install gateway[metrics] to run",
)
def test_metrics_returns_prometheus_format(gateway_client) -> None:
    """GET /metrics returns 200 and Prometheus text when metrics enabled and prometheus_client installed."""
    try:
        import prometheus_client  # noqa: F401
    except ImportError:
        pytest.skip("prometheus_client not installed")
    client = gateway_client
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "obr_http" in r.text or "http_requests" in r.text.lower()


def test_apply_patch_rejects_path_traversal(gateway_client) -> None:
    """apply_patch with a path containing '..' returns 400 and does not write outside workspace."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    fingerprint_id = open_resp.json()["fingerprint_id"]
    session_resp = client.post("/v1/sessions", json={"fingerprint_id": fingerprint_id})
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]

    apply_resp = client.post(
        f"/v1/sessions/{session_id}/apply-patch",
        json={"files": {"../escaped/file.lean": "content"}},
    )
    assert apply_resp.status_code == 400
    body = apply_resp.json()
    err = body.get("error", {})
    assert err.get("code") == "path_traversal"
    assert "escapes" in err.get("message", "")


def test_gateway_e2e_normalized_interactive_result(gateway_client) -> None:
    """E2E: open env (fixture), create session, apply_patch, interactive-check; response is normalized schema."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    fingerprint_id = open_resp.json()["fingerprint_id"]
    session_resp = client.post("/v1/sessions", json={"fingerprint_id": fingerprint_id})
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]

    apply_resp = client.post(
        f"/v1/sessions/{session_id}/apply-patch",
        json={"files": {"Mini/Basic.lean": "def foo := 1\n"}},
    )
    assert apply_resp.status_code == 200

    check_resp = client.post(
        f"/v1/sessions/{session_id}/interactive-check",
        json={"file_path": "Mini/Basic.lean"},
    )
    assert check_resp.status_code == 200
    data = check_resp.json()
    assert "phase" in data
    assert data["phase"] == "interactive"
    assert "ok" in data
    assert "diagnostics" in data
    assert "goals" in data
    assert "timing_ms" in data
    assert isinstance(data["diagnostics"], list)
    assert isinstance(data["goals"], list)


def test_batch_verify_returns_session_not_found_for_unknown_session(gateway_client) -> None:
    """batch-verify with unknown session_id returns 404 and stable code session_not_found."""
    client = gateway_client
    r = client.post("/v1/sessions/unknown-session-id/batch-verify", json={})
    assert r.status_code == 404
    assert r.json().get("error", {}).get("code") == "session_not_found"


def test_apply_patch_overlay_only_base_unchanged(gateway_client) -> None:
    """After apply_patch, overlay has new content; base snapshot is unchanged."""
    from pathlib import Path

    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    fingerprint_id = open_resp.json()["fingerprint_id"]
    session_resp = client.post("/v1/sessions", json={"fingerprint_id": fingerprint_id})
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    workspace_path = Path(session_resp.json()["workspace_path"])
    patched_content = "-- patched by test\n"
    apply_resp = client.post(
        f"/v1/sessions/{session_id}/apply-patch",
        json={"files": {"Mini/Basic.lean": patched_content}},
    )
    assert apply_resp.status_code == 200
    overlay_file = workspace_path / "Mini" / "Basic.lean"
    assert overlay_file.exists()
    assert patched_content in overlay_file.read_text(encoding="utf-8")
    base_path = Path(".var") / "environments" / fingerprint_id / "base" / "Mini" / "Basic.lean"
    if base_path.exists():
        assert patched_content not in base_path.read_text(encoding="utf-8")
