"""Minimal Lean 4 LSP client over stdio: diagnostics, goals, hover, definition. Used by LspLeanTransport.

Design: one long-lived LSP process per workspace (keyed by workspace_path), reused across
check/get_goal/hover/definition requests. Cache has a max size (default 8); LRU eviction
terminates the oldest process. Goal methods: $/lean/plainGoal and $/lean/plainTermGoal (Lean 4 LSP).
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from pathlib import Path

_LSP_CACHE: dict[str, tuple[subprocess.Popen, float]] = {}
_LSP_LOCK = threading.Lock()
_LSP_MAX_SIZE = 8


def _write(proc: subprocess.Popen, msg: dict) -> None:
    if proc.stdin is None:
        return
    body = json.dumps(msg, separators=(",", ":"))
    proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n{body}")
    proc.stdin.flush()


def _read(proc: subprocess.Popen, timeout_seconds: float) -> dict | None:
    if proc.stdout is None:
        return None
    line = proc.stdout.readline()
    if not line:
        return None
    if not line.strip().startswith("Content-Length:"):
        return None
    try:
        length = int(line.strip().split(":", 1)[1].strip())
    except (ValueError, IndexError):
        return None
    deadline = time.monotonic() + timeout_seconds
    data = []
    while length > 0 and time.monotonic() < deadline and proc.stdout:
        chunk = proc.stdout.read(min(length, 65536))
        if not chunk:
            break
        data.append(chunk)
        length -= len(chunk)
    body = "".join(data)
    if not body:
        return None
    return json.loads(body)


def _start_lsp(workspace_path: Path, timeout_seconds: float) -> subprocess.Popen | None:
    try:
        proc = subprocess.Popen(
            ["lean", "--server"],
            cwd=str(workspace_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError:
        return None
    _write(proc, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "processId": None,
            "rootUri": str(workspace_path.as_uri()),
            "capabilities": {},
        },
    })
    resp = _read(proc, timeout_seconds)
    if not resp or "result" not in resp:
        proc.terminate()
        proc.wait(timeout=2)
        return None
    _write(proc, {"jsonrpc": "2.0", "method": "initialized", "params": {}})
    return proc


def _evict_oldest() -> None:
    if not _LSP_CACHE:
        return
    oldest_key = min(_LSP_CACHE, key=lambda k: _LSP_CACHE[k][1])
    proc, _ = _LSP_CACHE.pop(oldest_key, (None, 0.0))
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def _get_or_create_lsp(workspace_path: Path, timeout_seconds: float) -> subprocess.Popen | None:
    """Get or create a long-lived LSP process for the workspace; reuse across requests."""
    key = str(workspace_path.resolve())
    with _LSP_LOCK:
        if key in _LSP_CACHE:
            proc, _ = _LSP_CACHE[key]
            if proc.poll() is not None:
                _LSP_CACHE.pop(key, None)
            else:
                _LSP_CACHE[key] = (proc, time.monotonic())
                return proc
        while len(_LSP_CACHE) >= _LSP_MAX_SIZE:
            _evict_oldest()
        new_proc = _start_lsp(workspace_path, timeout_seconds)
        if new_proc is not None:
            _LSP_CACHE[key] = (new_proc, time.monotonic())
        return new_proc


def _touch_lsp(workspace_path: Path) -> None:
    key = str(workspace_path.resolve())
    with _LSP_LOCK:
        if key in _LSP_CACHE:
            proc, _ = _LSP_CACHE[key]
            _LSP_CACHE[key] = (proc, time.monotonic())


def _uri(path: Path) -> str:
    return path.as_uri()


def run_check(
    workspace_path: Path,
    full_path: Path,
    timeout_seconds: float = 60.0,
) -> tuple[list[dict], list[dict], bool]:
    """Run LSP check: open file, wait for publishDiagnostics, return (diagnostics, goals, ok)."""
    proc = _get_or_create_lsp(workspace_path, timeout_seconds)
    if proc is None:
        return ([], [], False)
    try:
        if not full_path.exists():
            return ([], [], False)
        text = full_path.read_text(encoding="utf-8")
        uri = _uri(full_path)
        td = {"uri": uri, "languageId": "lean4", "version": 1, "text": text}
        _write(proc, {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {"textDocument": td},
        })
        diagnostics: list[dict] = []
        deadline = time.monotonic() + min(timeout_seconds, 30.0)
        while time.monotonic() < deadline:
            msg = _read(proc, 5.0)
            if msg is None:
                break
            if msg.get("method") == "textDocument/publishDiagnostics":
                params = msg.get("params") or {}
                for d in params.get("diagnostics", []):
                    r = d.get("range", {})
                    start = r.get("start", {})
                    end = r.get("end")
                    end_line = (end.get("line", 0) + 1) if end else None
                    end_col = end.get("character", 0) if end else None
                    diagnostics.append({
                        "severity": d.get("severity", 1),
                        "file": str(full_path),
                        "line": start.get("line", 0) + 1,
                        "column": start.get("character", 0),
                        "end_line": end_line,
                        "end_column": end_col,
                        "message": d.get("message", ""),
                        "source": "lean",
                    })
                break
            if "id" in msg and "result" in msg:
                break
        ok = not any(d.get("severity") == 1 for d in diagnostics)
        return (diagnostics, [], ok)
    finally:
        _touch_lsp(workspace_path)


def run_get_goal(
    workspace_path: Path,
    file_path: str,
    line: int,
    column: int,
    goal_kind: str,
    timeout_seconds: float,
) -> list[dict]:
    """Request goal at position; returns list of goal dicts (kind, text, file, line, column)."""
    full_path = workspace_path / file_path
    proc = _get_or_create_lsp(workspace_path, timeout_seconds)
    if proc is None:
        return []
    try:
        if not full_path.exists():
            return []
        text = full_path.read_text(encoding="utf-8")
        uri = _uri(full_path)
        td = {"uri": uri, "languageId": "lean4", "version": 1, "text": text}
        _write(proc, {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {"textDocument": td},
        })
        _read(proc, 5.0)
        method = "$/lean/plainGoal" if "plain" in goal_kind else "$/lean/plainTermGoal"
        _write(proc, {
            "jsonrpc": "2.0",
            "id": 2,
            "method": method,
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": column},
            },
        })
        resp = _read(proc, 10.0)
        if not resp or "result" not in resp:
            return []
        goals = resp.get("result")
        if goals is None:
            return []
        if isinstance(goals, list):
            return [g if isinstance(g, dict) else {"text": str(g)} for g in goals]
        if isinstance(goals, dict):
            entry = {
                "kind": goal_kind,
                "text": goals.get("text", str(goals)),
                "file": file_path,
                "line": line,
                "column": column,
            }
            return [entry]
        return []
    finally:
        _touch_lsp(workspace_path)


def run_hover(
    workspace_path: Path,
    file_path: str,
    line: int,
    column: int,
    timeout_seconds: float,
) -> str:
    """Request hover at position; returns contents string."""
    full_path = workspace_path / file_path
    proc = _get_or_create_lsp(workspace_path, timeout_seconds)
    if proc is None:
        return ""
    try:
        if not full_path.exists():
            return ""
        text = full_path.read_text(encoding="utf-8")
        uri = _uri(full_path)
        td = {"uri": uri, "languageId": "lean4", "version": 1, "text": text}
        _write(proc, {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {"textDocument": td},
        })
        _read(proc, 5.0)
        _write(proc, {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "textDocument/hover",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": column},
            },
        })
        resp = _read(proc, 10.0)
        if not resp or "result" not in resp:
            return ""
        result = resp["result"]
        if result is None:
            return ""
        if isinstance(result, dict) and "contents" in result:
            c = result["contents"]
            if isinstance(c, dict):
                return c.get("value", c)
            return str(c)
        return str(result)
    finally:
        _touch_lsp(workspace_path)


def run_definition(
    workspace_path: Path,
    file_path: str,
    line: int,
    column: int,
    timeout_seconds: float,
) -> list[dict]:
    """Request definition at position; returns list of location dicts."""
    full_path = workspace_path / file_path
    proc = _get_or_create_lsp(workspace_path, timeout_seconds)
    if proc is None:
        return []
    try:
        if not full_path.exists():
            return []
        text = full_path.read_text(encoding="utf-8")
        uri = _uri(full_path)
        td = {"uri": uri, "languageId": "lean4", "version": 1, "text": text}
        _write(proc, {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {"textDocument": td},
        })
        _read(proc, 5.0)
        _write(proc, {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "textDocument/definition",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": column},
            },
        })
        resp = _read(proc, 10.0)
        if not resp or "result" not in resp:
            return []
        result = resp["result"]
        if result is None:
            return []
        if isinstance(result, list):
            return [r for r in result if isinstance(r, dict)]
        if isinstance(result, dict):
            return [result]
        return []
    finally:
        _touch_lsp(workspace_path)
