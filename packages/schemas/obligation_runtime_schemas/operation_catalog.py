"""Canonical operation catalog for the Obligation Runtime API.

Single source of truth for operation names, parameters, and descriptions.
Used by MCP tool list, LangChain tools, and docs to avoid drift.
Paths are defined in api_paths.py.
"""

from __future__ import annotations

# Each entry: name (snake_case, matches SDK method), params, description. Paths live in api_paths.
OPERATIONS: list[dict] = [
    {
        "name": "open_environment",
        "params": ["repo_id", "repo_path", "repo_url", "commit_sha"],
        "description": "Open a Lean environment by repo_id (and optional repo_path, repo_url, commit_sha).",
    },
    {
        "name": "create_session",
        "params": ["fingerprint_id", "thread_id"],
        "description": "Create a session for a fingerprint.",
    },
    {
        "name": "apply_patch",
        "params": ["session_id", "thread_id", "files"],
        "description": "Apply patch (files) to session.",
    },
    {
        "name": "check_interactive",
        "params": ["session_id", "thread_id", "file_path"],
        "description": "Run interactive check on file.",
    },
    {
        "name": "get_goal",
        "params": ["session_id", "thread_id", "file_path", "line", "column", "goal_kind"],
        "description": "Get goal at position.",
    },
    {
        "name": "hover",
        "params": ["session_id", "thread_id", "file_path", "line", "column"],
        "description": "Get hover contents at position (LSP).",
    },
    {
        "name": "definition",
        "params": ["session_id", "thread_id", "file_path", "line", "column"],
        "description": "Get definition locations at position (LSP).",
    },
    {
        "name": "batch_verify",
        "params": ["session_id", "thread_id", "target_files", "target_declarations"],
        "description": "Run batch verification.",
    },
    {
        "name": "get_review_payload",
        "params": ["thread_id"],
        "description": "Get review payload for thread.",
    },
    {
        "name": "submit_review_decision",
        "params": ["thread_id", "decision"],
        "description": "Submit approve or reject for thread.",
    },
    {
        "name": "resume",
        "params": ["thread_id"],
        "description": "Resume graph after approve/reject (requires checkpointer).",
    },
]


def get_mcp_tool_name(operation_name: str) -> str:
    """Return MCP tool name for an operation (e.g. obligation/open_environment)."""
    return f"obligation/{operation_name}"


def operation_param_schema(param: str) -> dict:
    """Return JSON Schema type for common param names."""
    if param in ("line", "column"):
        return {"type": "integer"}
    if param in ("target_files", "target_declarations"):
        return {"type": "array", "items": {"type": "string"}}
    if param == "files":
        return {"type": "object"}
    return {"type": "string"}


def build_mcp_tool_schemas() -> list[dict]:
    """Build MCP tools/list payload from the operation catalog."""
    schemas = []
    for op in OPERATIONS:
        params = op.get("params", [])
        properties = {p: operation_param_schema(p) for p in params}
        schemas.append({
            "name": get_mcp_tool_name(op["name"]),
            "description": op.get("description", ""),
            "inputSchema": {"type": "object", "properties": properties},
        })
    return schemas
