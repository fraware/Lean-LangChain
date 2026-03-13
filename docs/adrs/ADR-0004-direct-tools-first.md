# ADR-0004 — Direct tools first

## Context

Agents need a stable way to call the Gateway (open environment, create session, batch verify, etc.). MCP is one possible transport, but V1 should not depend on it; the core runtime boundary should be the HTTP API and LangChain tools so that non-MCP clients are first-class.

## Decision

V1 uses direct service APIs and LangChain tools. MCP is added later as an adapter, not as the core runtime boundary.

## Consequences

- The Gateway HTTP API and SDK are the canonical interface; tools wrap them.
- MCP exposes the same operations via an adapter layer.

**See also:** [gateway-api.md](../architecture/gateway-api.md), [mcp-adapter.md](../architecture/mcp-adapter.md), [workflow.md](../workflow.md).
