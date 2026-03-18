# Architecture

High-level design and reference for the Obligation Runtime. Start with [core-primitives.md](core-primitives.md) and [runtime-graph.md](runtime-graph.md) to understand the flow; use the rest as needed.

| Document | Contents |
|----------|----------|
| [core-primitives.md](core-primitives.md) | Obligations, witnesses, environment, and policy. |
| [runtime-graph.md](runtime-graph.md) | LangGraph patch-admissibility flow: state, nodes, handoff, status. |
| [gateway-api.md](gateway-api.md) | Lean Gateway HTTP API: endpoints, health, OpenAPI. |
| [policy-model.md](policy-model.md) | PolicyEngine, policy packs, patch metadata, protocol evaluator. |
| [multi-agent-protocol.md](multi-agent-protocol.md) | Protocol events and obligation classes (handoff, review, lock, etc.). |
| [environment-model.md](environment-model.md) | Snapshots, overlays, workspace lifecycle. |
| [acceptance-lane.md](acceptance-lane.md) | Batch verification: build, axiom audit, fresh checker. |
| [interactive-lane.md](interactive-lane.md) | Per-file Lean check; informs repair, not the final gate. |
| [review-surface.md](review-surface.md) | Review API, UI, approve/reject, resume, webhooks. |
| [plugin-contract.md](plugin-contract.md) | Policy pack plugin contract (v1): load by name/path, versioning, stability. |
| [reviewer-gated-execution.md](reviewer-gated-execution.md) | When approval is required and how it is enforced. |
| [worker-isolation.md](worker-isolation.md) | Local, container, and microVM runners; resource limits. |
| [mcp-adapter.md](mcp-adapter.md) | MCP server: session affinity, tools, persistent store. |
| [telemetry-and-evals.md](telemetry-and-evals.md) | Tracing, LangSmith, evaluation corpus. |

**See also:** [../workflow.md](../workflow.md), [../glossary.md](../glossary.md).
