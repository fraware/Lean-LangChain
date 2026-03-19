# Glossary

Key terms used in the Lean-LangChain docs. For full definitions and data shapes, see the [architecture](architecture/) docs and [workflow.md](workflow.md).

| Term | Definition | See |
|------|------------|---------------|
| **Obligation** | A formally checkable claim attached to a workflow step (e.g. patch admissibility, handoff legality). | [core-primitives.md](architecture/core-primitives.md) |
| **EnvironmentFingerprint** | The exact Lean/Lake environment used to decide an obligation (repo, commit, toolchain, hashes). | [core-primitives.md](architecture/core-primitives.md), [environment-model.md](architecture/environment-model.md) |
| **WitnessBundle** | The evidence produced during decision-making: fingerprint, batch result, policy decision, approval if any. Produced on every accepted run. | [core-primitives.md](architecture/core-primitives.md) |
| **PolicyDecision** | Outcome of policy evaluation: `accepted`, `rejected`, `blocked`, `needs_review`, `lower_trust`, or `failed`. | [core-primitives.md](architecture/core-primitives.md), [policy-model.md](architecture/policy-model.md) |
| **acceptance lane** | The batch-verify path (lake build, axiom audit, fresh checker). The only final gate for acceptance; interactive check is never the final gate. | [acceptance-lane.md](architecture/acceptance-lane.md) |
| **interactive lane** | Per-file Lean check (LSP or subprocess) used for repair and diagnostics; informs but does not decide acceptance. | [interactive-lane.md](architecture/interactive-lane.md) |
| **policy pack** | Versioned YAML configuration (e.g. `strict_patch_gate_v1`) that defines protected paths, reviewer gating, and protocol checks. | [policy-model.md](architecture/policy-model.md) |
| **review payload** | Data pushed to the Gateway when the graph interrupts for human approval: patch_metadata, diagnostics, reasons. | [review-surface.md](architecture/review-surface.md) |
| **Resume run** | Action (UI button or `POST /v1/reviews/{thread_id}/resume`) that continues the graph after approve/reject; requires a checkpointer. | [review-surface.md](architecture/review-surface.md) |
| **Lean Gateway** | HTTP API that runs Lean in isolated workspaces: open environment, sessions, apply-patch, interactive check, batch verify, reviews. | [gateway-api.md](architecture/gateway-api.md) |
| **orchestrator** | CLI (`obr`) and LangGraph runtime that drives the patch-admissibility graph and talks to the Gateway via the SDK. | [workflow.md](workflow.md) |
| **Review UI** | Next.js app for viewing review payloads and submitting Approve/Reject and **Resume run**. Production: Docker image `infra/docker/review-ui.Dockerfile` or `npm run build` with `NEXT_PUBLIC_GATEWAY_URL`. | [running.md](running.md), [deployment.md](deployment.md) |
| **readiness** | `GET /ready`; when `REVIEW_STORE=postgres`, the Gateway checks database connectivity and returns 503 with `{"status": "not_ready", "reason": "database_unavailable"}` if Postgres is unreachable. | [gateway-api.md](architecture/gateway-api.md) |
| **test double** | In tests only: `TestDoubleTransport`, `AxiomAuditor`, `FreshChecker` injected via `deps.set_test_*()` in conftest. Production requires real transport and real axiom/fresh implementations (env-configured). | [interactive-lane.md](architecture/interactive-lane.md), [ADR-0006](adrs/ADR-0006-interactive-transport-boundary.md) |

See also: [workflow.md](workflow.md), [architecture/core-primitives.md](architecture/core-primitives.md), [README.md](../README.md).
