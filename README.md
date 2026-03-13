# lean-langchain

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A semantic control plane for high-stakes agent workflows: Lean-backed verification, policy packs, and human-in-the-loop review. Integrates with LangChain, LangGraph, and LangSmith so you can run, integrate, or extend verification and approval without reimplementing the pipeline.

**In this repo:** Lean Gateway (HTTP API), orchestrator CLI and LangGraph runtime, Review UI, Python/TypeScript SDKs, LangChain tools, policy and protocol packs, and demos.

---

## Table of contents

- [lean-langchain](#lean-langchain)
  - [Table of contents](#table-of-contents)
  - [Quick start](#quick-start)
  - [Running the stack](#running-the-stack)
  - [Repository layout](#repository-layout)
  - [Reusing this repo](#reusing-this-repo)
  - [Development](#development)
  - [Documentation](#documentation)
  - [License and design principles](#license-and-design-principles)

---

## Quick start

All commands assume you are at the repository root and use a single Python (e.g. an activated venv). If your venv has no pip, run `python -m ensurepip` once, then activate and install.

```bash
# Minimal install (schemas + gateway)
pip install -e packages/schemas -e apps/lean-gateway

# Full stack (recommended for development)
make install-dev-full

# Run checks
make check        # Lint, tests, schema export (no typecheck or regressions)
make check-full   # Full CI pipeline (lint, typecheck, all tests, export-schemas)
```

---

## Running the stack

| Component   | Command |
|------------|---------|
| **Gateway** | `uvicorn obligation_runtime_lean_gateway.api.app:app --reload` — API docs at `/docs`, `/redoc`. |
| **Review UI** | From `apps/review-ui`: `npm install && npm run dev`. Set `NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000`. Review at `http://localhost:3000/reviews/[threadId]`; use **Resume run** after Approve/Reject (or `obr resume <thread_id>` with a checkpointer). |
| **CLI** | `python -m obligation_runtime_orchestrator.cli` or `obr` — `open-environment`, `create-session`, `run-patch-obligation`, `review`, `resume`, `artifacts`, `regressions`. |

**Verification:** With the project venv activated, `make check-full` runs the full pipeline (lint, typecheck, schema/unit/integration/regression tests, export-schemas). For benchmarks: `make benchmark` or `make benchmark-report` (see [docs/tests-and-ci.md](docs/tests-and-ci.md)).

**Demo:** [docs/demos/main-demo.md](docs/demos/main-demo.md) — run `make demo-hero` or `make demo-hero-ui` (scenario 3 uses the Review UI and Postgres for resume).

---

## Repository layout

| Directory    | Contents |
|-------------|----------|
| **apps/**   | `lean-gateway` (FastAPI: environments, sessions, batch-verify, reviews, resume), `orchestrator` (CLI, LangGraph runtime, MCP server), `review-ui` (Next.js review UI with Approve/Reject and Resume run). |
| **packages/** | `schemas`, `sdk-py`, `sdk-ts`, `tools` (LangChain), `policy`, `evals`, `telemetry`. |
| **docs/**   | Architecture, runbooks, demos, [docs/README.md](docs/README.md) (index). |
| **tests/**  | Unit, integration, and regression tests; see [tests/README.md](tests/README.md) for layout and skips. |
| **examples/** | Minimal SDK usage ([hello_sdk_gateway.py](examples/hello_sdk_gateway.py)) and optional patch producers (fixture, OpenAI, Anthropic); see [examples/README.md](examples/README.md). |

Full agentic loops (LLM-driven drafting, repair, multi-agent workflows) can live in a separate repo; this one stays focused on verification and approval.

---

## Reusing this repo

To call an existing Obligation Runtime Gateway from Python, install the SDK and use `ObligationRuntimeClient`. [docs/integrate.md](docs/integrate.md) describes integration tiers: data contracts only, API client (recommended), LangChain tools, full graph, or hosting the Gateway. It also lists the public API and per-package imports.

---

## Development

| Command | Description |
|---------|-------------|
| `make lint` | Ruff (style and lint). |
| `make typecheck` | Mypy (schemas, gateway, orchestrator). |
| `make test` | Unit tests. |
| `make test-integration` | Integration tests. |
| `make test-regressions` | Regression golden tests. |
| `make test-axiom-producer` | Axiom producer test (requires `lake` in PATH; skips otherwise). |
| `make test-tracer-e2e` | Tracer E2E (requires `obligation-runtime-telemetry[otlp]`). |
| `make export-schemas` | Export JSON schemas. |
| `make check` | Quick check: lint, schema tests, unit, integration, export-schemas. |
| `make check-full` | Full check: lint, typecheck, all tests, export-schemas (same as CI). |

Demos: `make demo-scenario-1` … `make demo-scenario-5` ([docs/demos/README.md](docs/demos/README.md)). Setup: `make install-lean4checker` or `python scripts/setup/install_lean4checker.py`. Environment variables (OBR_GATEWAY_URL, CHECKPOINTER, DATABASE_URL, etc.): [docs/running.md](docs/running.md). Production: [docs/deployment.md](docs/deployment.md).

---

## Documentation

Start at [docs/README.md](docs/README.md) for the full index. By goal:

| Goal | Document |
|------|----------|
| Concepts and workflow | [workflow.md](docs/workflow.md) |
| Integration tiers | [integrate.md](docs/integrate.md) |
| Run and operate | [running.md](docs/running.md) |
| Production deploy | [deployment.md](docs/deployment.md) |

Further: [docs/architecture/](docs/architecture/), [docs/demos/](docs/demos/), [docs/tests-and-ci.md](docs/tests-and-ci.md), [docs/glossary.md](docs/glossary.md).

---

## License and design principles

This project is licensed under the MIT License — see [LICENSE](LICENSE).

Design principles:

- Lean is the only semantic authority.
- The interactive lane is never the final acceptance gate; batch verification is.
- The environment is the unit of reuse; every terminal decision emits a WitnessBundle.
- Human approval is triggered only by policy deltas.
- External boundaries use versioned schemas; no trace, no trust.
