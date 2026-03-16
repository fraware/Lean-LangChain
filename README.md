# lean-langchain

<div align="center">
  <img src="assets/Logo.png" alt="Lean LangChain" width="280" />
</div>

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A semantic control plane for high-stakes agent workflows.**

</div> When agents or tools propose changes to formal code, something has to decide whether those changes are correct. This project makes **Lean** that single authority: every patch is verified by Lean (build, axiom audit, fresh checker), policy can require human review for sensitive paths, and every decision produces auditable evidence. Integrates with LangChain, LangGraph, and LangSmith so you can run, integrate, or extend verification and approval without reimplementing the pipeline.

---

## Why this exists

Agents and automation are increasingly able to draft and edit code. For formal and proof-relevant code, "does it typecheck?" is not enough: you need a **reproducible, unambiguous verdict** and, for critical changes, a human in the loop. This repo provides that layer: a Gateway that runs Lean, an orchestrator that drives the verification graph, policy packs for protected paths and reviewer gating, and a Review UI. You supply the patch (from a human, a script, or an LLM); the runtime tells you accept or reject and gives you a WitnessBundle for every run. Full agentic loops (LLM-driven drafting, repair, multi-agent workflows) can live in a separate repo; this one stays focused on **verification and approval**.

---

## Table of contents

- [lean-langchain](#lean-langchain)
  - [Why this exists](#why-this-exists)
  - [Table of contents](#table-of-contents)
  - [What's in this repo](#whats-in-this-repo)
  - [Quick start](#quick-start)
  - [Running the stack](#running-the-stack)
  - [Demos](#demos)
  - [Reusing this repo](#reusing-this-repo)
  - [Repository layout](#repository-layout)
  - [Development](#development)
  - [Documentation](#documentation)
  - [Contributing](#contributing)
  - [License and design principles](#license-and-design-principles)

---

## What's in this repo

| Component | Description |
|-----------|-------------|
| **Lean Gateway** | HTTP API: open environment, create session, apply patch, interactive check, batch verify, reviews and resume. |
| **Orchestrator** | CLI (`obr`) and LangGraph runtime that drive the patch-admissibility graph and call the Gateway. |
| **Review UI** | Next.js app to approve or reject runs that touch protected paths, then resume the graph. |
| **SDKs and tools** | Python and TypeScript SDKs; LangChain tools so agents can call the same operations. |
| **Policy and protocol** | Versioned policy packs (protected paths, reviewer gating); protocol obligations (handoff, lock, etc.). |
| **Demos** | Core demo (good patch, sorry rejected, protected path + review) and full demo (6-step proof-preserving gate). |

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

| Component | Command |
|-----------|---------|
| **Gateway** | `uvicorn obligation_runtime_lean_gateway.api.app:app --reload` — API docs at `/docs`, `/redoc`. |
| **Review UI** | From `apps/review-ui`: `npm install && npm run dev`. Set `NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000`. Review at `http://localhost:3000/reviews/[threadId]`; use **Resume run** after Approve/Reject (or `obr resume <thread_id>` with a checkpointer). |
| **CLI** | `python -m obligation_runtime_orchestrator.cli` or `obr` — `open-environment`, `create-session`, `run-patch-obligation`, `review`, `resume`, `artifacts`, `regressions`. |

With the project venv activated, `make check-full` runs the full pipeline (lint, typecheck, schema/unit/integration/regression tests, export-schemas). For benchmarks: `make benchmark` or `make benchmark-report` (see [docs/tests-and-ci.md](docs/tests-and-ci.md)).

---

## Demos

- **Core demo** — Good patch accepted, sorry patch rejected, protected path paused for human review. [docs/demos/main-demo.md](docs/demos/main-demo.md). Run: `make demo-core` or `make demo-core-ui`.
- **Full demo** — Six steps: no patch, valid proof edit, sorry, false theorem, protected approve/reject, evidence export. [docs/demos/full-demo.md](docs/demos/full-demo.md). Run: `make demo-full` or `make demo-full-ui`.

Both require the Gateway to be running; scenario 3 (core) and steps 5–6 (full) need Postgres for resume. Individual scenarios: `make demo-scenario-1` … `make demo-scenario-5` ([docs/demos/README.md](docs/demos/README.md)).

---

## Reusing this repo

To call an existing Obligation Runtime Gateway from Python, install the SDK and use `ObligationRuntimeClient`. [docs/integrate.md](docs/integrate.md) describes integration tiers: data contracts only, API client (recommended), LangChain tools, full graph, or hosting the Gateway. It also lists the public API and per-package imports.

---

## Repository layout

| Directory | Contents |
|-----------|----------|
| **apps/** | `lean-gateway` (FastAPI), `orchestrator` (CLI, LangGraph runtime, MCP server), `review-ui` (Next.js). |
| **packages/** | `schemas`, `sdk-py`, `sdk-ts`, `tools` (LangChain), `policy`, `evals`, `telemetry`. |
| **docs/** | Architecture, runbooks, demos; [docs/README.md](docs/README.md) (index). |
| **tests/** | Unit, integration, and regression tests; [tests/README.md](tests/README.md). |
| **examples/** | Minimal SDK usage ([minimal_sdk_gateway.py](examples/minimal_sdk_gateway.py)); [examples/README.md](examples/README.md). Demos live in **scripts/demos/** and [docs/demos/](docs/demos/). |

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

Demos: `make demo-core`, `make demo-full`. Setup: `make install-lean4checker` or `python scripts/setup/install_lean4checker.py`. Environment variables: [docs/running.md](docs/running.md). Production: [docs/deployment.md](docs/deployment.md).

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

## Contributing

We want this to become the default way teams gate formal and proof-relevant changes: one pipeline, one semantic authority (Lean), optional human review, and evidence for every decision. Getting there needs more adopters, more backends (e.g. other provers or typecheckers), and more integrations. 

We welcome contributions: code, documentation, feedback, and ideas. Run the full check before submitting (`make check-full`). See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, code style, and pull request process. If you use this in production or research, we would love to hear how; opening an issue or discussion is a good way to share.

---

## License and design principles

This project is licensed under the MIT License — see [LICENSE](LICENSE).

Design principles:

- Lean is the only semantic authority.
- The interactive lane is never the final acceptance gate; batch verification is.
- The environment is the unit of reuse; every terminal decision emits a WitnessBundle.
- Human approval is triggered only by policy deltas.
- External boundaries use versioned schemas; no trace, no trust.
