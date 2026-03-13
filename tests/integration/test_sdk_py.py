"""Integration tests for Python SDK against Gateway API (TestClient)."""

from pathlib import Path

from obligation_runtime_sdk.client import ObligationRuntimeClient


def test_sdk_e2e_against_gateway(sdk_client: ObligationRuntimeClient) -> None:
    """SDK open_environment, create_session, apply_patch, interactive_check, batch_verify return expected shapes."""
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    client = sdk_client

    open_data = client.open_environment(repo_id="lean-mini", repo_path=str(repo_path), commit_sha="head")
    assert "fingerprint_id" in open_data
    assert "fingerprint" in open_data
    fingerprint_id = open_data["fingerprint_id"]

    session_data = client.create_session(fingerprint_id=fingerprint_id)
    assert "session_id" in session_data
    assert session_data.get("fingerprint_id") == fingerprint_id
    session_id = session_data["session_id"]

    apply_data = client.apply_patch(session_id=session_id, files={"Mini/Basic.lean": "def x := 1\n"})
    assert "ok" in apply_data
    assert "changed_files" in apply_data

    check_data = client.interactive_check(session_id=session_id, file_path="Mini/Basic.lean")
    assert "ok" in check_data
    assert "phase" in check_data
    assert "diagnostics" in check_data
    assert "goals" in check_data

    batch_data = client.batch_verify(session_id=session_id, target_files=["Mini/Basic.lean"], target_declarations=[])
    assert "ok" in batch_data
    assert "trust_level" in batch_data
    assert "build" in batch_data
    assert "axiom_audit" in batch_data
    assert "fresh_checker" in batch_data
    assert "reasons" in batch_data
