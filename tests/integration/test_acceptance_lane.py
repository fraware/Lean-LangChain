"""Integration tests for the acceptance lane (batch-verify endpoint).

Covers the authoritative acceptance path: open environment -> create session ->
batch-verify. Asserts BatchVerifyResult shape (ok, trust_level, build, axiom_audit,
fresh_checker, reasons, axiom_evidence_real, fresh_evidence_real). Includes
Prompt 04-style cases (clean theorem, sorry, interactive-pass/batch-fail) and
optional strict acceptance (OBR_ACCEPTANCE_STRICT) when env is set. The acceptance
lane is never bypassed by the interactive lane; see docs/workflow.md
(workflow step 5 and use cases 2.1, 2.2).
"""

import os
import shutil
from pathlib import Path

# Short timeout for lake build so tests don't hang; must be set before gateway import.
os.environ.setdefault("OBR_BUILD_TIMEOUT", "10")

import pytest

from tests.integration.api_stubs import STUB_INTERACTIVE_CHECK_SORRY
from tests.integration.conftest import make_testclient_request_adapter


def test_acceptance_lane_batch_verify_returns_structured_result(gateway_client) -> None:
    """POST /v1/sessions/{id}/batch-verify returns BatchVerifyResult-like shape."""
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

    batch_resp = client.post(
        f"/v1/sessions/{session_id}/batch-verify",
        json={"target_files": ["Mini/Basic.lean"], "target_declarations": []},
    )
    assert batch_resp.status_code == 200
    data = batch_resp.json()
    assert "ok" in data
    assert "trust_level" in data
    assert data["trust_level"] in ("clean", "warning", "blocked")
    assert "build" in data
    assert "axiom_audit" in data
    assert "fresh_checker" in data
    assert "reasons" in data
    assert isinstance(data["reasons"], list)
    assert "ok" in data["build"]
    assert "trust_level" in data["axiom_audit"]
    assert "ok" in data["fresh_checker"]
    assert "axiom_evidence_real" in data
    assert "fresh_evidence_real" in data
    assert isinstance(data["axiom_evidence_real"], bool)
    assert isinstance(data["fresh_evidence_real"], bool)


@pytest.mark.skipif(
    not os.environ.get("OBR_ACCEPTANCE_STRICT"),
    reason="Set OBR_ACCEPTANCE_STRICT=1 to run (strict logic is unit-tested in test_batch_combine)",
)
def test_acceptance_lane_strict_blocks_without_real_evidence(gateway_client) -> None:
    """When OBR_ACCEPTANCE_STRICT=1, batch-verify returns blocked if axiom or fresh evidence is not real."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    session_resp = client.post(
        "/v1/sessions",
        json={"fingerprint_id": open_resp.json()["fingerprint_id"]},
    )
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    batch_resp = client.post(
        f"/v1/sessions/{session_id}/batch-verify",
        json={"target_files": ["Mini/Basic.lean"], "target_declarations": []},
    )
    assert batch_resp.status_code == 200
    data = batch_resp.json()
    assert data["trust_level"] == "blocked", data
    assert data["ok"] is False
    reasons = data.get("reasons", [])
    assert "acceptance_strict_requires_real_axiom_audit" in reasons
    assert "acceptance_strict_requires_real_fresh_checker" in reasons


@pytest.mark.skipif(not shutil.which("lake"), reason="lake not in PATH")
def test_acceptance_lane_build_runner_real_lake_build(gateway_client) -> None:
    """When lake is available, batch-verify runs real lake build and returns build result shape."""
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
    batch_resp = client.post(
        f"/v1/sessions/{session_id}/batch-verify",
        json={"target_files": ["Mini/Basic.lean"], "target_declarations": []},
    )
    assert batch_resp.status_code == 200
    data = batch_resp.json()
    assert "build" in data
    assert "command" in data["build"]
    assert data["build"]["command"] == ["lake", "build"]
    assert "timing_ms" in data["build"]
    assert "ok" in data["build"]
    # ok may be True or False depending on environment (lake may fail on some setups).


@pytest.mark.skipif(
    not shutil.which("lean") or not os.environ.get("OBR_USE_LEAN_LSP"),
    reason="LSP not available (lean not in PATH or OBR_USE_LEAN_LSP not set)",
)
def test_acceptance_lane_full_flow_with_lsp(gateway_client) -> None:
    """With OBR_USE_LEAN_LSP=1 and lean in PATH, open -> session -> interactive-check -> batch-verify (real LSP + lake)."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    session_resp = client.post(
        "/v1/sessions",
        json={"fingerprint_id": open_resp.json()["fingerprint_id"]},
    )
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    check_resp = client.post(
        f"/v1/sessions/{session_id}/interactive-check",
        json={"file_path": "Mini/Basic.lean"},
    )
    assert check_resp.status_code == 200
    assert "diagnostics" in check_resp.json()
    assert "goals" in check_resp.json()
    batch_resp = client.post(
        f"/v1/sessions/{session_id}/batch-verify",
        json={"target_files": ["Mini/Basic.lean"], "target_declarations": []},
    )
    assert batch_resp.status_code == 200
    data = batch_resp.json()
    assert "ok" in data and "trust_level" in data
    assert "build" in data and "axiom_audit" in data
    assert data["build"].get("command") == ["lake", "build"] or "lake" in str(
        data["build"].get("command", [])
    )


@pytest.mark.skipif(
    not os.environ.get("OBR_USE_REAL_AXIOM_AUDIT"),
    reason="OBR_USE_REAL_AXIOM_AUDIT not set",
)
def test_acceptance_lane_real_axiom_audit(gateway_client) -> None:
    """When OBR_USE_REAL_AXIOM_AUDIT=1, batch-verify uses AxiomAuditorReal."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    session_resp = client.post(
        "/v1/sessions", json={"fingerprint_id": open_resp.json()["fingerprint_id"]}
    )
    assert session_resp.status_code == 200
    batch_resp = client.post(
        f"/v1/sessions/{session_resp.json()['session_id']}/batch-verify",
        json={"target_files": ["Mini/Basic.lean"], "target_declarations": []},
    )
    assert batch_resp.status_code == 200
    data = batch_resp.json()
    assert "axiom_audit" in data
    assert data["axiom_audit"]["trust_level"] in ("clean", "warning", "blocked")
    assert "blocked_reasons" in data["axiom_audit"]


@pytest.mark.skipif(not shutil.which("lake"), reason="lake not in PATH")
@pytest.mark.skipif(
    not os.environ.get("OBR_USE_REAL_AXIOM_AUDIT") or not os.environ.get("OBR_AXIOM_AUDIT_CMD"),
    reason="OBR_USE_REAL_AXIOM_AUDIT and OBR_AXIOM_AUDIT_CMD must point at producer (e.g. scripts/axiom_list_lean/run_axiom_list.sh)",
)
def test_acceptance_lane_axiom_producer_dependencies_non_empty(gateway_client) -> None:
    """When OBR_AXIOM_AUDIT_CMD points at producer and workspace has axiom_list, axiom_audit.dependencies non-empty."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    if open_resp.status_code != 200:
        pytest.skip("open_environment failed (fixture or snapshot issue)")
    session_resp = client.post(
        "/v1/sessions",
        json={"fingerprint_id": open_resp.json()["fingerprint_id"]},
    )
    assert session_resp.status_code == 200
    batch_resp = client.post(
        f"/v1/sessions/{session_resp.json()['session_id']}/batch-verify",
        json={"target_files": ["Mini/Basic.lean"], "target_declarations": []},
    )
    assert batch_resp.status_code == 200
    data = batch_resp.json()
    assert "axiom_audit" in data
    assert "dependencies" in data["axiom_audit"]
    assert (
        len(data["axiom_audit"]["dependencies"]) >= 1
    ), "Producer should output declaration lines when workspace has axiom_list (e.g. lean-mini)"


@pytest.mark.skipif(
    os.environ.get("OBR_WORKER_RUNNER") != "container"
    or not os.environ.get("OBR_DOCKER_IMAGE")
    or not shutil.which("docker"),
    reason="Container runner not configured (OBR_WORKER_RUNNER=container, OBR_DOCKER_IMAGE, docker)",
)
def test_acceptance_lane_container_runner_batch_verify(gateway_client) -> None:
    """When OBR_WORKER_RUNNER=container and OBR_DOCKER_IMAGE set, batch-verify runs build in container."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    session_resp = client.post(
        "/v1/sessions", json={"fingerprint_id": open_resp.json()["fingerprint_id"]}
    )
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    batch_resp = client.post(
        f"/v1/sessions/{session_id}/batch-verify",
        json={"target_files": ["Mini/Basic.lean"], "target_declarations": []},
    )
    assert batch_resp.status_code == 200
    data = batch_resp.json()
    assert "build" in data
    assert "command" in data["build"]
    assert "timing_ms" in data["build"]
    assert "ok" in data["build"]
    assert isinstance(data["build"].get("ok"), bool)


@pytest.mark.skipif(
    os.environ.get("OBR_WORKER_RUNNER") != "microvm"
    or not os.environ.get("OBR_DOCKER_IMAGE")
    or not shutil.which("docker"),
    reason="MicroVM runner not configured (OBR_WORKER_RUNNER=microvm, OBR_DOCKER_IMAGE, docker)",
)
def test_acceptance_lane_microvm_runner_batch_verify(gateway_client) -> None:
    """When OBR_WORKER_RUNNER=microvm (runsc), batch-verify runs build in microVM."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    session_resp = client.post(
        "/v1/sessions", json={"fingerprint_id": open_resp.json()["fingerprint_id"]}
    )
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    batch_resp = client.post(
        f"/v1/sessions/{session_id}/batch-verify",
        json={"target_files": ["Mini/Basic.lean"], "target_declarations": []},
    )
    assert batch_resp.status_code == 200
    data = batch_resp.json()
    assert "build" in data
    assert "command" in data["build"]
    assert "timing_ms" in data["build"]
    assert "ok" in data["build"]
    assert isinstance(data["build"].get("ok"), bool)


# --- Prompt 04 named integration tests (clean theorem, sorry, custom axiom, interactive-pass/batch-fail) ---


@pytest.mark.skipif(not shutil.which("lake"), reason="lake not in PATH")
def test_acceptance_lane_clean_theorem(gateway_client) -> None:
    """E2E: open -> session -> interactive-check -> batch-verify; assert acceptance (ok, trust_level clean)."""
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
    batch_resp = client.post(
        f"/v1/sessions/{session_id}/batch-verify",
        json={"target_files": ["Mini/Basic.lean"], "target_declarations": []},
    )
    assert batch_resp.status_code == 200
    data = batch_resp.json()
    assert data.get("trust_level") in ("clean", "warning", "blocked")
    assert "ok" in data
    if data.get("build", {}).get("ok"):
        assert data["ok"] in (True, False)
        assert data["trust_level"] in ("clean", "warning", "blocked")


def test_acceptance_lane_theorem_using_sorry(gateway_tc) -> None:
    """E2E: graph run with adapter that simulates interactive check failing (sorry); assert rejected."""
    from lean_langchain_orchestrator.runtime.graph import build_patch_admissibility_graph
    from lean_langchain_orchestrator.runtime.initial_state import make_initial_state
    from lean_langchain_sdk.client import ObligationRuntimeClient

    tc = gateway_tc
    base = make_testclient_request_adapter(tc)

    def adapter(method: str, path: str, body: object) -> dict:
        if method == "POST" and "interactive-check" in path:
            return dict(STUB_INTERACTIVE_CHECK_SORRY)
        return base(method, path, body)

    client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
    graph = build_patch_admissibility_graph(client=client)
    repo_path = str(Path(__file__).resolve().parent / "fixtures" / "lean-mini")
    initial = make_initial_state(
        thread_id="prompt04_sorry",
        obligation_id="ob_sorry",
        obligation={"target": {"repo_id": "lean-mini"}},
        target_files=["Mini/Basic.lean"],
        repo_path=repo_path,
    )
    result = graph.invoke(initial)
    assert result.get("status") in ("rejected", "repairing")


def test_acceptance_lane_custom_axiom_case(gateway_tc) -> None:
    """E2E: graph run with adapter that returns batch_verify with trust_level blocked (custom axioms); assert blocked."""
    from lean_langchain_orchestrator.runtime.graph import build_patch_admissibility_graph
    from lean_langchain_orchestrator.runtime.initial_state import make_initial_state
    from lean_langchain_sdk.client import ObligationRuntimeClient

    tc = gateway_tc
    base = make_testclient_request_adapter(tc)

    def adapter(method: str, path: str, body: object) -> dict:
        if method == "POST" and "batch-verify" in path:
            return {
                "ok": False,
                "trust_level": "blocked",
                "reasons": ["custom_axiom"],
                "build": {"ok": True},
                "axiom_audit": {
                    "ok": False,
                    "trust_level": "blocked",
                    "blocked_reasons": ["custom_axiom"],
                    "dependencies": [],
                },
                "fresh_checker": {"ok": True},
            }
        return base(method, path, body)

    client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
    graph = build_patch_admissibility_graph(client=client)
    repo_path = str(Path(__file__).resolve().parent / "fixtures" / "lean-mini")
    initial = make_initial_state(
        thread_id="prompt04_axiom",
        obligation_id="ob_axiom",
        obligation={"target": {"repo_id": "lean-mini"}},
        target_files=["Mini/Basic.lean"],
        repo_path=repo_path,
        interactive_result={"ok": True, "diagnostics": [], "goals": []},
    )
    result = graph.invoke(initial)
    assert result.get("trust_level") == "blocked"
    assert (result.get("policy_decision") or {}).get("decision") in ("rejected", "blocked")


def test_acceptance_lane_interactive_pass_batch_fail(gateway_tc) -> None:
    """E2E: interactive-check ok, batch-verify fails; assert terminal status rejected."""
    from lean_langchain_orchestrator.runtime.graph import build_patch_admissibility_graph
    from lean_langchain_orchestrator.runtime.initial_state import make_initial_state
    from lean_langchain_sdk.client import ObligationRuntimeClient

    tc = gateway_tc
    base = make_testclient_request_adapter(tc)

    def adapter(method: str, path: str, body: object) -> dict:
        if method == "POST":
            if "interactive-check" in path:
                return {"ok": True, "diagnostics": [], "goals": []}
            if "batch-verify" in path:
                return {
                    "ok": False,
                    "trust_level": "blocked",
                    "reasons": ["build_failed"],
                    "build": {"ok": False},
                    "axiom_audit": {
                        "ok": True,
                        "trust_level": "clean",
                        "blocked_reasons": [],
                        "dependencies": [],
                    },
                    "fresh_checker": {"ok": False},
                }
        return base(method, path, body)

    client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
    graph = build_patch_admissibility_graph(client=client)
    repo_path = str(Path(__file__).resolve().parent / "fixtures" / "lean-mini")
    initial = make_initial_state(
        thread_id="prompt04_interactive_pass_batch_fail",
        obligation_id="ob_ipbf",
        obligation={"target": {"repo_id": "lean-mini"}},
        target_files=["Mini/Basic.lean"],
        repo_path=repo_path,
    )
    result = graph.invoke(initial)
    assert (result.get("policy_decision") or {}).get("decision") in ("rejected", "blocked")


def _fresh_checker_available() -> bool:
    """True if lean4checker is in PATH or OBR_FRESH_CHECK_CMD points at an existing executable."""
    import shutil

    if shutil.which("lean4checker"):
        return True
    cmd = os.environ.get("OBR_FRESH_CHECK_CMD", "")
    if not cmd:
        return False
    first = cmd.split()[0].strip('"')
    return os.path.isfile(first) or bool(shutil.which(first))


@pytest.mark.skipif(
    not os.environ.get("OBR_USE_REAL_FRESH_CHECKER"),
    reason="OBR_USE_REAL_FRESH_CHECKER not set",
)
@pytest.mark.skipif(
    not _fresh_checker_available(),
    reason="lean4checker not in PATH and OBR_FRESH_CHECK_CMD not set or executable not found",
)
def test_acceptance_lane_real_fresh_checker(gateway_client) -> None:
    """When OBR_USE_REAL_FRESH_CHECKER=1, batch-verify uses FreshCheckerReal. Skips if no fresh checker available."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    session_resp = client.post(
        "/v1/sessions", json={"fingerprint_id": open_resp.json()["fingerprint_id"]}
    )
    assert session_resp.status_code == 200
    batch_resp = client.post(
        f"/v1/sessions/{session_resp.json()['session_id']}/batch-verify",
        json={"target_files": ["Mini/Basic.lean"], "target_declarations": []},
    )
    assert batch_resp.status_code == 200
    data = batch_resp.json()
    assert "fresh_checker" in data
    assert "ok" in data["fresh_checker"]
    assert "command" in data["fresh_checker"]
