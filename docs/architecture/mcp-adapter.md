# MCP adapter

The MCP server exposes the same Gateway operations as tools, with session affinity: the session can be restored by `thread_id` after reconnect. Optional store: memory, Redis, or Postgres.

## Session affinity

- **MCPSessionContext** holds the current session for MCP tool calls: `session_id`, `thread_id`, `fingerprint_id`, `workspace_path`. Tools that need a session (apply_patch, check_interactive, get_goal, batch_verify) resolve the session via `_session_id(session_id, thread_id)`: they accept optional `session_id` and optional `thread_id`; when context is empty, the store is consulted so that a client can send only `thread_id` after a reconnect and the server restores the session from the persistent store.
- **create_session** accepts optional `thread_id`; when provided, it is stored in context and persisted so that later tool calls can restore by `thread_id`.

## Persistence

- **MCPSessionStore** (see `obligation_runtime_orchestrator.mcp_session_store`): backends are **memory** (default), **redis**, or **postgres**. Set `OBR_MCP_SESSION_STORE=redis` or `postgres`; Redis uses `OBR_REDIS_URL`; Postgres uses `DATABASE_URL` or `REVIEW_STORE_POSTGRES_URI`. On `create_session`, the gateway returns `session_id` and the store records `session_id`, `thread_id` (if provided), `fingerprint_id`, `workspace_path`. Lookup supports both `session_id` and `thread_id` so that clients can restore by either after a restart.

## Tool parameters

- **obligation/create_session:** `fingerprint_id`, optional `thread_id`.
- **obligation/apply_patch**, **obligation/check_interactive**, **obligation/get_goal**, **obligation/batch_verify:** optional `session_id`, optional `thread_id` (for restore when context is empty), plus their usual parameters (e.g. `files`, `file_path`, `target_files`, `target_declarations`).

**Tool return shape:** MCP tool handlers normalize SDK responses to **JSON-shaped dicts** (`model_dump(mode="json")`) for the MCP wire format. Unit tests may use plain dict doubles for the client; both are accepted.

Tests: `tests/unit/test_mcp_session_restore.py` (restore by thread_id after simulated restart), `tests/integration/test_mcp_session_affinity.py`.

**See also:** [gateway-api.md](gateway-api.md), [workflow.md](../workflow.md), [running.md](../running.md).
