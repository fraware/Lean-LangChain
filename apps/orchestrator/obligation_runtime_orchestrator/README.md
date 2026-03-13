# Orchestrator

**Purpose:** LangGraph patch-admissibility runtime, CLI (`obr`), checkpointer integration, witness builder, and MCP adapter. **Audience:** integrators and operators.

This package provides the graph, checkpointer (MemorySaver or PostgresSaver), witness builder, CLI (`obr`), and MCP adapter. The graph computes patch_metadata from `summarize_patch`, evaluates V2 protocol obligation classes when protocol_events are present, and interrupts for approval when policy returns needs_review. Resume is supported in-process or via Postgres checkpointer.

**See also:** [docs/architecture/runtime-graph.md](../../../docs/architecture/runtime-graph.md), [docs/demos/README.md](../../../docs/demos/README.md), [docs/workflow.md](../../../docs/workflow.md).
