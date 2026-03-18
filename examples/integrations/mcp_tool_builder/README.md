# MCP tool-builder integration

Use the Obligation Runtime Gateway as a set of MCP tools so an MCP client (e.g. Cline, another agent) can call open_environment, create_session, apply_patch, batch_verify, review, resume, etc.

**Prerequisites:** Gateway running (e.g. `uvicorn obligation_runtime_lean_gateway.api.app:app`). Set `OBR_GATEWAY_URL` (see [docs/running.md](../../../docs/running.md) builder configuration).

**Run:** From repo root with the full env installed (`make install-dev-full`), run the script with a gateway URL:

```bash
export OBR_GATEWAY_URL=http://localhost:8000
python examples/integrations/mcp_tool_builder/run_mcp_tools.py
```

Or integrate `build_mcp_tools(client, context, store)` into your own MCP server; tool names are `obligation/open_environment`, `obligation/create_session`, etc. (see [operation_catalog](../../packages/schemas/obligation_runtime_schemas/operation_catalog.py)).
