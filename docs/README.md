# Documentation

Navigation for all docs in this repo. Start from your goal below.

## By goal

| Goal | Start here |
|------|------------|
| **New to the project** | Root [README](../README.md) → [workflow.md](workflow.md) → [demos/main-demo.md](demos/main-demo.md) or [demos/full-demo.md](demos/full-demo.md) |
| **Integrate the runtime** | [integrate.md](integrate.md) → [architecture/gateway-api.md](architecture/gateway-api.md) → [running.md](running.md) |
| **Deploy to production** | [deployment.md](deployment.md) → [running.md](running.md) |
| **Contribute or run tests** | [CONTRIBUTING.md](../CONTRIBUTING.md) → [tests-and-ci.md](tests-and-ci.md) |

## Core docs

- **[workflow.md](workflow.md)** — End-to-end workflow, use cases, and how the runtime fits with LangChain, LangSmith, and LangGraph.
- **[integrate.md](integrate.md)** — Integration tiers (schemas only, API client, LangChain tools, full graph, host Gateway) and public API. Recommended entry: API client.
- **[running.md](running.md)** — Setup, starting the Gateway and Review UI, environment variables, CLI, MCP, resume, production checklist, workers.
- **[deployment.md](deployment.md)** — Build, configure, deploy, and verify a production stack (Compose or Kubernetes).
- **[tests-and-ci.md](tests-and-ci.md)** — Local check commands, CI jobs, and benchmark script.
- **[glossary.md](glossary.md)** — Key terms (obligation, witness, acceptance lane, etc.).

## Architecture

See [architecture/README.md](architecture/README.md) for an index. Main entries: [core-primitives](architecture/core-primitives.md), [runtime-graph](architecture/runtime-graph.md), [gateway-api](architecture/gateway-api.md).

## Demos

- **[demos/main-demo.md](demos/main-demo.md)** — Core demo: verification and human review (good patch, sorry rejected, protected path); `make demo-core`, `make demo-core-ui`.
- **[demos/full-demo.md](demos/full-demo.md)** — Full demo: proof-preserving patch gate (6 steps; valid edit, sorry, false theorem, protected approve/reject, evidence export); `make demo-full`, `make demo-full-ui`.
- **[demos/README.md](demos/README.md)** — All scenarios (1–5), protocol demos, and regression commands.

## Runbooks (advanced)

- **[runbooks/evaluation.md](runbooks/evaluation.md)** — LangSmith experiments and regression corpus.
- **[runbooks/observability.md](runbooks/observability.md)** — Prometheus metrics, alerts, minimal dashboard.

## For maintainers

- **[releasing.md](releasing.md)** — Versioning, compatibility policy, tagging, release workflow, artifact publication (PyPI, npm, OCI).
- **adrs/** — Architecture decision records: Lean as authority, two-lane execution, obligation policy, tools-first, snapshots, interactive transport.

**See also:** [README](../README.md), [CONTRIBUTING.md](../CONTRIBUTING.md), [SECURITY.md](../SECURITY.md).
