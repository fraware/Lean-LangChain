"""Unit tests for Lean 4 LSP client (lsp_client.py) with mocked subprocess. No Lean required."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from obligation_runtime_lean_gateway.server import lsp_client


def _make_stdout(*responses: dict) -> io.StringIO:
    """Build a fake stdout that yields Content-Length-framed JSON-RPC messages.
    Format: Content-Length: N\\r\\n then N bytes of body (no extra \\r\\n)."""
    out = io.StringIO()
    for msg in responses:
        body = json.dumps(msg, separators=(",", ":"))
        out.write(f"Content-Length: {len(body)}\r\n{body}")
    out.seek(0)
    return out


def _workspace_path() -> Path:
    """Path valid for as_uri() on all platforms."""
    return (Path(__file__).resolve().parent / "ws").resolve()


def test_start_lsp_returns_none_when_initialize_fails() -> None:
    """_start_lsp returns None when initialize response is missing or invalid."""
    with patch("obligation_runtime_lean_gateway.server.lsp_client.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = io.StringIO()  # no content -> _read returns None
        proc.stderr = MagicMock()
        mock_popen.return_value = proc

        result = lsp_client._start_lsp(_workspace_path(), 5.0)
    assert result is None


def test_start_lsp_returns_proc_when_initialize_ok() -> None:
    """_start_lsp returns process when initialize returns result."""
    init_resp = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
    stdout = _make_stdout(init_resp)
    with patch("obligation_runtime_lean_gateway.server.lsp_client.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = stdout
        proc.stderr = MagicMock()
        mock_popen.return_value = proc

        result = lsp_client._start_lsp(_workspace_path(), 5.0)
    assert result is proc
    mock_popen.assert_called_once()
    call_kw = mock_popen.call_args[1]
    assert "cwd" in call_kw
    assert mock_popen.call_args[0][0] == ["lean", "--server"]


def test_run_check_returns_diagnostics_and_ok_from_publish_diagnostics() -> None:
    """run_check parses publishDiagnostics and derives ok from severity (1 = error)."""
    init_resp = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
    diag = {
        "method": "textDocument/publishDiagnostics",
        "params": {
            "diagnostics": [
                {
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 0, "character": 5},
                    },
                    "severity": 1,
                    "message": "error msg",
                }
            ]
        },
    }
    stdout = _make_stdout(init_resp, diag)
    with patch("obligation_runtime_lean_gateway.server.lsp_client.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = stdout
        proc.stderr = MagicMock()
        mock_popen.return_value = proc

        tmp = Path(__file__).resolve().parent
        fake_file = tmp / "fake.lean"
        fake_file.write_text("example", encoding="utf-8")
        try:
            diags, goals, ok = lsp_client.run_check(tmp, fake_file, timeout_seconds=5.0)
        finally:
            if fake_file.exists():
                fake_file.unlink()

    assert len(diags) == 1
    assert diags[0]["message"] == "error msg"
    assert diags[0]["severity"] == 1
    assert diags[0]["line"] == 1
    assert ok is False  # severity 1 = Error -> not ok


def test_run_check_ok_true_when_no_error_severity() -> None:
    """run_check sets ok=True when no diagnostic has severity 1."""
    init_resp = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
    diag = {"method": "textDocument/publishDiagnostics", "params": {"diagnostics": []}}
    stdout = _make_stdout(init_resp, diag)
    with patch("obligation_runtime_lean_gateway.server.lsp_client.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = stdout
        proc.stderr = MagicMock()
        mock_popen.return_value = proc

        tmp = Path(__file__).resolve().parent
        fake_file = tmp / "fake2.lean"
        fake_file.write_text("example", encoding="utf-8")
        try:
            diags, goals, ok = lsp_client.run_check(tmp, fake_file, timeout_seconds=5.0)
        finally:
            if fake_file.exists():
                fake_file.unlink()

    assert ok is True
    assert len(diags) == 0


def test_run_get_goal_returns_list_from_array_result() -> None:
    """run_get_goal returns list of goals when LSP result is array."""
    init_resp = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
    after_did_open = {"method": "textDocument/publishDiagnostics", "params": {"diagnostics": []}}
    goal_resp = {"jsonrpc": "2.0", "id": 2, "result": [{"text": "goal 1"}]}
    stdout = _make_stdout(init_resp, after_did_open, goal_resp)
    with patch("obligation_runtime_lean_gateway.server.lsp_client.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = stdout
        proc.stderr = MagicMock()
        mock_popen.return_value = proc

        tmp = Path(__file__).resolve().parent
        fake_file = tmp / "Mini" / "Basic.lean"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.write_text("theorem t : True := trivial", encoding="utf-8")
        try:
            goals = lsp_client.run_get_goal(tmp, "Mini/Basic.lean", 0, 0, "plainGoal", 5.0)
        finally:
            if fake_file.exists():
                fake_file.unlink()
            if fake_file.parent.exists() and not any(fake_file.parent.iterdir()):
                fake_file.parent.rmdir()

    assert len(goals) == 1
    assert goals[0].get("text") == "goal 1"


def test_run_get_goal_normalizes_single_dict_to_list() -> None:
    """run_get_goal normalizes result {'text': 'single goal'} to list of one dict."""
    init_resp = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
    after_did_open = {"method": "textDocument/publishDiagnostics", "params": {"diagnostics": []}}
    goal_resp = {"jsonrpc": "2.0", "id": 2, "result": {"text": "single goal"}}
    stdout = _make_stdout(init_resp, after_did_open, goal_resp)
    with patch("obligation_runtime_lean_gateway.server.lsp_client.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = stdout
        proc.stderr = MagicMock()
        mock_popen.return_value = proc

        tmp = Path(__file__).resolve().parent
        fake_file = tmp / "Mini" / "Basic2.lean"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.write_text("theorem t : True := trivial", encoding="utf-8")
        try:
            goals = lsp_client.run_get_goal(tmp, "Mini/Basic2.lean", 0, 0, "plainGoal", 5.0)
        finally:
            if fake_file.exists():
                fake_file.unlink()

    assert len(goals) == 1
    assert goals[0].get("text") == "single goal"


def test_run_get_goal_uses_plain_goal_method_when_plain_in_kind() -> None:
    """run_get_goal sends $/lean/plainGoal when goal_kind contains 'plain'."""
    init_resp = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
    after_did_open = {"method": "textDocument/publishDiagnostics", "params": {}}
    goal_resp = {"jsonrpc": "2.0", "id": 2, "result": []}
    stdout = _make_stdout(init_resp, after_did_open, goal_resp)
    with patch("obligation_runtime_lean_gateway.server.lsp_client.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = stdout
        proc.stderr = MagicMock()
        mock_popen.return_value = proc

        tmp = Path(__file__).resolve().parent
        fake_file = tmp / "Mini" / "Basic3.lean"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.write_text("theorem t : True := trivial", encoding="utf-8")
        try:
            lsp_client.run_get_goal(tmp, "Mini/Basic3.lean", 0, 0, "plainGoal", 5.0)
            payload = "".join(c[0][0] for c in proc.stdin.write.call_args_list)
            assert "$/lean/plainGoal" in payload
        finally:
            if fake_file.exists():
                fake_file.unlink()


def test_run_get_goal_uses_plain_term_goal_when_plain_not_in_kind() -> None:
    """run_get_goal sends $/lean/plainTermGoal when goal_kind does not contain 'plain'."""
    init_resp = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
    after_did_open = {"method": "textDocument/publishDiagnostics", "params": {}}
    goal_resp = {"jsonrpc": "2.0", "id": 2, "result": []}
    stdout = _make_stdout(init_resp, after_did_open, goal_resp)
    with patch("obligation_runtime_lean_gateway.server.lsp_client.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = stdout
        proc.stderr = MagicMock()
        mock_popen.return_value = proc

        tmp = Path(__file__).resolve().parent
        fake_file = tmp / "Mini" / "Basic4.lean"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.write_text("theorem t : True := trivial", encoding="utf-8")
        try:
            lsp_client.run_get_goal(tmp, "Mini/Basic4.lean", 0, 0, "termGoal", 5.0)
            payload = "".join(c[0][0] for c in proc.stdin.write.call_args_list)
            assert "$/lean/plainTermGoal" in payload
        finally:
            if fake_file.exists():
                fake_file.unlink()


def test_run_hover_returns_contents_value() -> None:
    """run_hover returns the string from result.contents.value."""
    init_resp = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
    after_did_open = {"method": "textDocument/publishDiagnostics", "params": {}}
    hover_resp = {"jsonrpc": "2.0", "id": 3, "result": {"contents": {"value": "hover text"}}}
    stdout = _make_stdout(init_resp, after_did_open, hover_resp)
    with patch("obligation_runtime_lean_gateway.server.lsp_client.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = stdout
        proc.stderr = MagicMock()
        mock_popen.return_value = proc

        tmp = Path(__file__).resolve().parent
        fake_file = tmp / "Mini" / "Hover.lean"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.write_text("theorem t : True := trivial", encoding="utf-8")
        try:
            text = lsp_client.run_hover(tmp, "Mini/Hover.lean", 0, 0, 5.0)
        finally:
            if fake_file.exists():
                fake_file.unlink()

    assert text == "hover text"


def test_run_definition_returns_list_of_locations() -> None:
    """run_definition returns list of location dicts from result."""
    init_resp = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
    after_did_open = {"method": "textDocument/publishDiagnostics", "params": {}}
    def_resp = {
        "jsonrpc": "2.0",
        "id": 4,
        "result": [
            {
                "uri": "file:///path/to/file.lean",
                "range": {
                    "start": {"line": 10, "character": 0},
                    "end": {"line": 10, "character": 5},
                },
            }
        ],
    }
    stdout = _make_stdout(init_resp, after_did_open, def_resp)
    with patch("obligation_runtime_lean_gateway.server.lsp_client.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = stdout
        proc.stderr = MagicMock()
        mock_popen.return_value = proc

        tmp = Path(__file__).resolve().parent
        fake_file = tmp / "Mini" / "Def.lean"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.write_text("theorem t : True := trivial", encoding="utf-8")
        try:
            locs = lsp_client.run_definition(tmp, "Mini/Def.lean", 0, 0, 5.0)
        finally:
            if fake_file.exists():
                fake_file.unlink()

    assert len(locs) == 1
    assert locs[0]["uri"] == "file:///path/to/file.lean"
    assert "range" in locs[0]
