"""Integration tests for Python SDK against Gateway API (TestClient)."""

from pathlib import Path

from lean_langchain_sdk.client import ObligationRuntimeClient


def test_sdk_e2e_against_gateway(sdk_client: ObligationRuntimeClient) -> None:
    """SDK open_environment, create_session, apply_patch, interactive_check, batch_verify return expected shapes."""
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    client = sdk_client

    open_data = client.open_environment(
        repo_id="lean-mini", repo_path=str(repo_path), commit_sha="head"
    )
    assert open_data.fingerprint_id
    assert open_data.fingerprint is not None
    fingerprint_id = open_data.fingerprint_id

    session_data = client.create_session(fingerprint_id=fingerprint_id)
    assert session_data.session_id
    assert session_data.fingerprint_id == fingerprint_id
    session_id = session_data.session_id

    apply_data = client.apply_patch(
        session_id=session_id, files={"Mini/Basic.lean": "def x := 1\n"}
    )
    assert apply_data.ok is not None
    assert apply_data.changed_files is not None

    check_data = client.interactive_check(session_id=session_id, file_path="Mini/Basic.lean")
    assert check_data.ok is not None
    assert check_data.phase
    assert check_data.diagnostics is not None
    assert check_data.goals is not None

    batch_data = client.batch_verify(
        session_id=session_id, target_files=["Mini/Basic.lean"], target_declarations=[]
    )
    assert batch_data.ok is not None
    assert batch_data.trust_level
    assert batch_data.build is not None
    assert batch_data.axiom_audit is not None
    assert batch_data.fresh_checker is not None
    assert batch_data.reasons is not None
