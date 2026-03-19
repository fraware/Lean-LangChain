<p align="center">
  <img src="assets/Logo.png" alt="Lean-LangChain" width="200" />
</p>

<p align="center">
  <strong>Lean-LangChain</strong> — A semantic control plane for high-stakes agent workflows.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT" /></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+" /></a>
</p>

---

When agents or tools propose changes to formal code, something must decide whether those changes are correct. This project makes **Lean** that single authority: every patch is verified by Lean (build, axiom audit, fresh checker), policy can require human review for sensitive paths, and every decision produces auditable evidence. It integrates with LangChain, LangGraph, and LangSmith so you can run, integrate, or extend verification and approval without reimplementing the pipeline.

**Names:** Product and packages are **Lean-LangChain**; PyPI root is **lean-langchain**; npm SDK is **`@lean-langchain/sdk`**.

---

## Why Lean-LangChain

Agents and automation increasingly draft and edit code. For formal and proof-relevant code, “does it typecheck?” is not enough: you need a **reproducible, unambiguous verdict** and, for critical changes, a human in the loop. This repo provides that layer:

- **Gateway** — Runs Lean and exposes an HTTP API for environments, sessions, patches, and batch verification.
- **Orchestrator** — CLI and LangGraph runtime that drive the patch-admissibility graph and call the Gateway.
- **Policy packs** — Protected paths, reviewer gating, and versioned protocol obligations.
- **Review UI** — Approve or reject runs that touch protected paths, then resume the graph.

You supply the patch (from a human, a script, or an LLM); the runtime returns accept or reject and a **WitnessBundle** for every run. Full agentic loops can live elsewhere; this repo stays focused on **verification and approval**.

---

## What’s in this repo

| Component | Description |
|-----------|-------------|
| **Lean Gateway** | HTTP API: open environment, create session, apply patch, interactive check, batch verify, reviews and resume. |
| **Orchestrator** | CLI (`obr`) and LangGraph runtime for the patch-admissibility graph. |
| **Review UI** | Next.js app to approve/reject runs on protected paths and resume the graph. |
| **SDKs and tools** | Python and TypeScript SDKs; LangChain tools for the same operations. |
| **Policy and protocol** | Versioned packs (protected paths, reviewer gating); protocol obligations (handoff, lock, etc.). |
| **Demos** | Core demo (good patch, sorry rejected, protected path + review) and full 6-step proof-preserving demo. |

---

## Quick start

Use a single Python environment (e.g. activated venv) from the repo root. If your venv has no pip, run `python -m ensurepip` once.

```bash
# Minimal: schemas + gateway
pip install -e packages/schemas -e apps/lean-gateway

# Full stack (recommended for development)
make install-dev-full

# Run checks
make check        # Lint, tests, schema/OpenAPI export
make check-full   # Full CI gate (includes mypy, regressions, TS SDK parity; needs Node)
```

---

## Running the stack

| Component | Command |
|-----------|---------|
| **Gateway** | `uvicorn lean_langchain_gateway.api.app:app --reload` — API docs at `/docs`, `/redoc`. |
| **Review UI** | From `apps/review-ui`: `npm install && npm run dev`. Set `NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000`. |
| **CLI** | `python -m lean_langchain_orchestrator.cli` or `obr` — `open-environment`, `create-session`, `run-patch-obligation`, `review`, `resume`, `artifacts`, `regressions`. |

With the venv activated, `make check-full` runs the full CI gate. Benchmarks: `make benchmark` or `make benchmark-report` ([docs/tests-and-ci.md](docs/tests-and-ci.md)).

---

## Demos

| Demo | Description | Run |
|------|-------------|-----|
| **Core** | Good patch accepted, sorry rejected, protected path paused for review. | `make demo-core` or `make demo-core-ui` |
| **Full** | Six steps: no patch, valid proof edit, sorry, false theorem, protected approve/reject, evidence export. | `make demo-full` or `make demo-full-ui` |

Both require the Gateway. Scenario 3 (core) and steps 5–6 (full) need Postgres for resume. Details: [docs/demos/main-demo.md](docs/demos/main-demo.md), [docs/demos/full-demo.md](docs/demos/full-demo.md). Individual scenarios: `make demo-scenario-1` … `make demo-scenario-5` ([docs/demos/README.md](docs/demos/README.md)).

---

## Reusing this repo

To call an existing Lean-LangChain Gateway from Python, install the SDK and use `ObligationRuntimeClient`. [docs/integrate.md](docs/integrate.md) covers integration tiers: data contracts only, API client (recommended), LangChain tools, full graph, or hosting the Gateway, plus the public API and per-package imports.

---

## Repository layout

| Path | Contents |
|------|----------|
| **Root** | [pyproject.toml](pyproject.toml): workspace metapackage `lean_langchain`, shared Ruff/Black/mypy/pytest config, optional extras. |
| **apps/** | `lean-gateway` (FastAPI), `orchestrator` (CLI, LangGraph, MCP), `review-ui` (Next.js). |
| **packages/** | `schemas`, `sdk-py`, `sdk-ts`, `tools`, `policy`, `protocol`, `evals`, `telemetry`. |
| **contracts/** | OpenAPI snapshot and JSON schemas; regenerated via `make export-openapi` / `make export-schemas`. |
| **docs/** | Architecture, runbooks, demos — [docs/README.md](docs/README.md). |
| **tests/** | Unit, integration, regression — [tests/README.md](tests/README.md). |
| **examples/** | [minimal_sdk_gateway.py](examples/minimal_sdk_gateway.py); integration starters in [examples/integrations/](examples/integrations/README.md). |

---

## Development

| Command | Description |
|---------|-------------|
| `make lint` | Ruff (style and lint). |
| `make typecheck` | Mypy (schemas, gateway, orchestrator). |
| `make test` | Unit tests. |
| `make test-integration` | Integration tests. |
| `make test-regressions` | Regression golden tests. |
| `make export-schemas` | Export JSON schemas. |
| `make check` | Lint, schema tests, unit, integration, export-schemas. |
| `make check-full` | Full CI: lint, typecheck, strict-core mypy, all tests, export schemas/OpenAPI, verify TS SDK (needs Node). |

Demos: `make demo-core`, `make demo-full`. Environment: [docs/running.md](docs/running.md). Production: [docs/deployment.md](docs/deployment.md).

---

## Documentation

| Goal | Document |
|------|----------|
| Concepts and workflow | [workflow.md](docs/workflow.md) |
| Integration tiers | [integrate.md](docs/integrate.md) |
| Run and operate | [running.md](docs/running.md), [runtime capabilities](docs/operations/runtime-capabilities.md) |
| Production deploy | [deployment.md](docs/deployment.md) |
| Releases | [releasing.md](docs/releasing.md) |

More: [docs/architecture/](docs/architecture/), [docs/demos/](docs/demos/), [docs/tests-and-ci.md](docs/tests-and-ci.md), [docs/glossary.md](docs/glossary.md).

---

## Contributing

We want this to become the default way teams gate formal and proof-relevant changes: one pipeline, one semantic authority (Lean), optional human review, and evidence for every decision.

Contributions are welcome: code, documentation, feedback, and ideas. Run `make check-full` before submitting. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, code style, and pull request process.

---

## License and design principles

**License:** [MIT](LICENSE).

- **Lean is the only semantic authority.**
- The interactive lane is never the final acceptance gate; batch verification is.
- The environment is the unit of reuse; every terminal decision emits a WitnessBundle.
- Human approval is triggered only by policy deltas.
- External boundaries use versioned schemas; no trace, no trust.
