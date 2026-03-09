from __future__ import annotations

from pathlib import Path

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


@router.post("/sessions/{session_id}/apply-patch")
def apply_patch(session_id: str, payload: dict) -> dict:
    lease = deps.session_manager.get(session_id)
    files: dict[str, str] = payload["files"]
    for rel_path, content in files.items():
        path = lease.workspace_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return {"ok": True, "session_id": session_id, "changed_files": sorted(files.keys())}


@router.post("/sessions/{session_id}/interactive-check")
def interactive_check(session_id: str, payload: dict) -> dict:
    result = deps.interactive_api.check_interactive(session_id=session_id, file_path=payload["file_path"])
    return result.model_dump(mode="json")


@router.post("/sessions/{session_id}/goal")
def goal(session_id: str, payload: dict) -> dict:
    # Placeholder until real Lean transport goal querying is implemented.
    return {
        "ok": True,
        "goal_kind": payload.get("goal_kind", "plainGoal"),
        "goals": [],
        "line": payload["line"],
        "column": payload["column"],
    }


@router.post("/sessions/{session_id}/hover")
def hover(session_id: str, payload: dict) -> dict:
    return {"ok": True, "contents": "", "file_path": payload["file_path"], "line": payload["line"], "column": payload["column"]}


@router.post("/sessions/{session_id}/definition")
def definition(session_id: str, payload: dict) -> dict:
    return {"ok": True, "locations": [], "file_path": payload["file_path"], "line": payload["line"], "column": payload["column"]}
