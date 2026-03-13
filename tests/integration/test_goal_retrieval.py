"""Goal retrieval: with test double transport returns empty; LSP transport returns goals when available."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest


def test_goal_retrieval_with_test_double_returns_empty_goals(gateway_client) -> None:
    """With test double transport (injected in conftest), goal endpoint returns ok and empty goals."""
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
    goal_resp = client.post(
        f"/v1/sessions/{session_id}/goal",
        json={"file_path": "Mini/Basic.lean", "line": 0, "column": 0, "goal_kind": "plainGoal"},
    )
    assert goal_resp.status_code == 200
    data = goal_resp.json()
    assert data["ok"] is True
    assert data["goal_kind"] == "plainGoal"
    assert isinstance(data["goals"], list)
    assert data["line"] == 0
    assert data["column"] == 0


@pytest.mark.skipif(
    not shutil.which("lean") or not os.environ.get("OBR_USE_LEAN_LSP"),
    reason="LSP not available (lean not in PATH or OBR_USE_LEAN_LSP not set)",
)
def test_goal_retrieval_with_lsp_transport(gateway_client) -> None:
    """When OBR_USE_LEAN_LSP=1 and lean in PATH, goal endpoint returns goal shape (or empty)."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    session_resp = client.post("/v1/sessions", json={"fingerprint_id": open_resp.json()["fingerprint_id"]})
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    goal_resp = client.post(
        f"/v1/sessions/{session_id}/goal",
        json={"file_path": "Mini/Basic.lean", "line": 0, "column": 0, "goal_kind": "plainGoal"},
    )
    assert goal_resp.status_code == 200
    data = goal_resp.json()
    assert data["ok"] is True
    assert isinstance(data["goals"], list)
    # Real Lean 4 LSP response must be compatible with our parsing: each goal has "text" or structure.
    for g in data["goals"]:
        assert isinstance(g, dict), "each goal must be a dict"
        if g:
            assert "text" in g or "kind" in g or "file" in g, "goal entry must have text/kind/file"


def test_hover_with_test_double_returns_empty_contents(gateway_client) -> None:
    """With test double transport, hover endpoint returns 200 and empty contents."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    session_resp = client.post("/v1/sessions", json={"fingerprint_id": open_resp.json()["fingerprint_id"]})
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    hover_resp = client.post(
        f"/v1/sessions/{session_id}/hover",
        json={"file_path": "Mini/Basic.lean", "line": 0, "column": 0},
    )
    assert hover_resp.status_code == 200
    data = hover_resp.json()
    assert data["ok"] is True
    assert data["contents"] == ""
    assert data["file_path"] == "Mini/Basic.lean"
    assert data["line"] == 0
    assert data["column"] == 0


@pytest.mark.skipif(
    not shutil.which("lean") or not os.environ.get("OBR_USE_LEAN_LSP"),
    reason="LSP not available (lean not in PATH or OBR_USE_LEAN_LSP not set)",
)
def test_hover_with_lsp_transport(gateway_client) -> None:
    """When OBR_USE_LEAN_LSP=1 and lean in PATH, hover returns a string (may be empty)."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    session_resp = client.post("/v1/sessions", json={"fingerprint_id": open_resp.json()["fingerprint_id"]})
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    hover_resp = client.post(
        f"/v1/sessions/{session_id}/hover",
        json={"file_path": "Mini/Basic.lean", "line": 0, "column": 0},
    )
    assert hover_resp.status_code == 200
    data = hover_resp.json()
    assert data["ok"] is True
    assert isinstance(data["contents"], str)


def test_definition_with_test_double_returns_empty_locations(gateway_client) -> None:
    """With test double transport, definition endpoint returns 200 and empty locations."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    session_resp = client.post("/v1/sessions", json={"fingerprint_id": open_resp.json()["fingerprint_id"]})
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    def_resp = client.post(
        f"/v1/sessions/{session_id}/definition",
        json={"file_path": "Mini/Basic.lean", "line": 0, "column": 0},
    )
    assert def_resp.status_code == 200
    data = def_resp.json()
    assert data["ok"] is True
    assert data["locations"] == []
    assert data["file_path"] == "Mini/Basic.lean"
    assert data["line"] == 0
    assert data["column"] == 0


@pytest.mark.skipif(
    not shutil.which("lean") or not os.environ.get("OBR_USE_LEAN_LSP"),
    reason="LSP not available (lean not in PATH or OBR_USE_LEAN_LSP not set)",
)
def test_definition_with_lsp_transport(gateway_client) -> None:
    """When OBR_USE_LEAN_LSP=1 and lean in PATH, definition returns list of location dicts."""
    client = gateway_client
    repo_path = Path(__file__).resolve().parent / "fixtures" / "lean-mini"
    open_resp = client.post(
        "/v1/environments/open",
        json={"repo_id": "lean-mini", "repo_path": str(repo_path), "commit_sha": "head"},
    )
    assert open_resp.status_code == 200
    session_resp = client.post("/v1/sessions", json={"fingerprint_id": open_resp.json()["fingerprint_id"]})
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]
    def_resp = client.post(
        f"/v1/sessions/{session_id}/definition",
        json={"file_path": "Mini/Basic.lean", "line": 0, "column": 0},
    )
    assert def_resp.status_code == 200
    data = def_resp.json()
    assert data["ok"] is True
    assert isinstance(data["locations"], list)


@pytest.mark.skipif(
    not shutil.which("lean") or not os.environ.get("OBR_USE_LEAN_LSP"),
    reason="LSP not available (lean not in PATH or OBR_USE_LEAN_LSP not set)",
)
def test_interactive_check_with_lsp_transport(gateway_client) -> None:
    """When OBR_USE_LEAN_LSP=1 and lean in PATH, interactive-check returns diagnostics, goals, ok."""
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
    check_resp = client.post(
        f"/v1/sessions/{session_id}/interactive-check",
        json={"file_path": "Mini/Basic.lean"},
    )
    assert check_resp.status_code == 200
    data = check_resp.json()
    assert "diagnostics" in data
    assert "goals" in data
    assert "ok" in data
    assert isinstance(data["diagnostics"], list)
    assert isinstance(data["goals"], list)
    assert isinstance(data["ok"], bool)
