# Integration starters

Production-grade templates for extending or embedding Lean-LangChain. Use these as copy-paste bases for your own integrations. Prerequisites: from repo root, `make install-dev-full` (installs all packages plus dev tools via the root `[dev]` extra) and a running Gateway (`uvicorn lean_langchain_gateway.api.app:app`). See [docs/running.md](../../docs/running.md) for the builder configuration table.

## Cookbook (copy-paste)

| Goal | Command (from repo root) |
|------|--------------------------|
| Call Gateway from Python (minimal) | `OBR_GATEWAY_URL=http://localhost:8000 python examples/minimal_sdk_gateway.py` |
| MCP tools against Gateway | `OBR_GATEWAY_URL=http://localhost:8000 python examples/integrations/mcp_tool_builder/run_mcp_tools.py` |
| Run graph from Python | `OBR_GATEWAY_URL=http://localhost:8000 python examples/integrations/langgraph_embed/run_graph.py` |
| Use custom policy pack | `OBR_POLICY_PACK=/path/to/custom_strict_v1.yaml obr run-patch-obligation --thread-id demo --target-files Main.lean` |

## Templates

| Template | Purpose |
|----------|---------|
| [mcp_tool_builder](mcp_tool_builder/) | Wire the Gateway into your own MCP server or add obligation tools alongside other tools. |
| [langgraph_embed](langgraph_embed/) | Run the patch-admissibility graph inside your app (Python) with a Gateway URL. |
| [policy_pack_extension](policy_pack_extension/) | Ship a custom policy pack (YAML) and load it via path or `OBR_POLICY_PACK`. |

See [docs/integrate.md](../../docs/integrate.md) for integration tiers and [docs/architecture/](../../docs/architecture/) for API and graph details.
