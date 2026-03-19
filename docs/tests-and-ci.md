# Tests and CI

How to run checks locally and what the CI pipeline does. Use the same Python/venv as for install; run from repo root.

## Local commands

- **Quick check:** `make check` — Lint, schema tests, unit tests, integration tests, JSON schema export, OpenAPI export. No typecheck or regressions.
- **Full check:** `make check-full` — Lint; Mypy (`make typecheck` + `make typecheck-strict-core`); schema round-trip tests; unit, integration, and regression tests; JSON schema export; OpenAPI export; **`verify-openapi-sdk-contract`** (regenerates TS types from OpenAPI, `git diff` must be clean). Requires **Node.js** for the last step.

CI **main** job runs `make check-full` plus extra steps (Postgres-backed tests, contract pytest modules, tracer tests). Typecheck covers `packages/schemas`, `apps/lean-gateway`, and `apps/orchestrator`; strict Mypy covers policy, gateway batch/routes, orchestrator graph/MCP, and selected modules (see Makefile).

## Main CI job

The **main** job runs the full check with Postgres so the production persistence path is validated:

- Postgres 16 service with `DATABASE_URL`, `REVIEW_STORE=postgres`, `CHECKPOINTER=postgres`.
- Steps: `make install-dev-full` (includes root `[dev]` extra), extra Postgres deps, `make check-full`, gateway/orchestrator boundary tests, contract parity and OpenAPI snapshot tests, production tracer tests, Postgres review store and checkpointer tests.

A **contract** job (Node 20) runs cross-surface parity tests, TypeScript SDK unit tests, and `verify-openapi-sdk-contract`.

Unit tests do not require real API keys; when LangSmith is missing or auth fails, helpers return `status: "error"`. The main job uses test doubles for transport, axiom auditor, and fresh checker so the Gateway runs without Lean.

## Optional CI jobs

- **postgres** — Postgres review store and checkpointer tests only.
- **lean** — Installs Lean 4 via elan; runs LSP goal test, real lake build, and full flow (open, session, interactive-check, batch-verify) with a real Lean tree.
- **fresh** — Installs Lean 4 and lean4checker; runs real fresh-checker integration test.
- **container** — Builds worker image, runs container runner batch-verify test, then verifies no OBR-labeled containers remain (leak check).
- **gateway-image** — Builds Gateway image, runs docker-compose, verifies `/health` and `/ready`, then tears down.
- **telemetry-e2e** — Tracer unit tests and E2E with InMemorySpanExporter. Marked continue-on-error.
- **langsmith** — Runs when `LANGCHAIN_API_KEY` is set. LangSmith unit and fixed-corpus integration tests. Local: `make test-langsmith`.

Other targets: `make test-axiom-producer` (axiom producer in lean-mini), `make test-tracer-e2e` (requires `[otlp]` extra).

## Make targets

| Target | Description |
|--------|--------------|
| `check` | Lint, test-schemas, test, test-integration, export-schemas. |
| `check-full` | Lint, typecheck, test-schemas, test, test-integration, test-regressions, export-schemas. |
| `test-langsmith` | LangSmith unit and fixed-corpus integration tests. |
| `test-axiom-producer` | Axiom producer test (lean-mini; skips if lake absent). |
| `test-tracer-e2e` | Tracer E2E (requires obligation-runtime-telemetry[otlp]). |
| `demo-core` | Core demo (good patch, sorry, protected path); requires Gateway. See [demos/README.md](demos/README.md). |
| `demo-full` | Full demo (6-step proof-preserving gate); requires Gateway and Postgres for steps 5–6. |

To run the same as CI locally: activate venv, then `make install-dev-full` and `make check-full`. For Postgres tests locally: start Postgres, set `DATABASE_URL`, `REVIEW_STORE=postgres`, `CHECKPOINTER=postgres`, then run the Postgres test modules. See **tests/README.md** for environment-dependent skips.

## Benchmark

From repo root (same Python as install):

```bash
# Pipeline only (lint, typecheck, tests, export-schemas)
python scripts/run_benchmark.py

# Pipeline + workload (N graph invocations; latency and throughput)
python scripts/run_benchmark.py --workload 5

# Slowest tests
python scripts/run_benchmark.py --slowest 10

# Write report
python scripts/run_benchmark.py --output benchmark_report.json
```

Make: `make benchmark` (pipeline only), `make benchmark-report` (pipeline + workload 5, writes to docs/benchmark_report.json).

Reported metrics include lint/typecheck/test timings and pass/fail, and (with `--workload`) latency percentiles and throughput. With `OBR_METRICS_ENABLED=1` and the metrics extra, the Gateway exposes `GET /metrics` (request count, latency) at runtime.

**See also:** [running.md](running.md), [workflow.md](workflow.md), [CONTRIBUTING.md](../CONTRIBUTING.md).
