# Running and configuration

How to set up, run, and operate the Gateway, Review UI, CLI, and MCP. For deployment to production, see [deployment.md](deployment.md).

Copy [.env.example](../.env.example) to `.env` (never commit `.env`) for a compact list of environment variables. Details below.

## Setup

Run all commands from the repository root. Use the same Python for install and for `make`: activate your venv (Windows: `.\.venv\Scripts\Activate.ps1`; Unix: `source .venv/bin/activate`), then `make install-dev-full` and `make check-full`. See the root [README](../README.md) Quick start.

## Starting the Gateway

```bash
uvicorn obligation_runtime_lean_gateway.api.app:app --reload
```

Default: `http://127.0.0.1:8000`. OpenAPI: `http://127.0.0.1:8000/docs`. Health: `GET /health` (liveness), `GET /ready` (readiness).

**Docker Compose (Gateway + Postgres):** From repo root, `docker compose -f infra/docker/docker-compose.yml up -d`. Set `OBR_CORS_ORIGINS` for the Review UI origin. For local UI: `NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000`.

## Environment variables

- **OBR_GATEWAY_URL** — Gateway base URL (e.g. `http://localhost:8000`). Used by `obr` CLI and SDK. Default: `http://localhost:8000`.
- **NEXT_PUBLIC_GATEWAY_URL** — Review UI: Gateway URL for API calls. Set in `apps/review-ui/.env.local` or shell before `npm run dev`.
- **OBR_USE_REAL_LEAN** — Gateway uses subprocess: interactive check runs `lake build`; goal/hover/definition empty. Use for batch verification without LSP.
- **OBR_USE_LEAN_LSP** — Gateway uses LSP: interactive check and goal/hover/definition talk to Lean 4 LSP. Requires `lean` in PATH.
- **OBR_USE_REAL_AXIOM_AUDIT** — Acceptance uses real axiom audit (command in workspace). Override with **OBR_AXIOM_AUDIT_CMD** (e.g. script that runs `lake exe axiom_list`). See `scripts/axiom_list_lean/README.md`.
- **OBR_ACCEPTANCE_STRICT** — When set, batch-verify requires both real axiom audit and real fresh checker; otherwise returns `trust_level: blocked`.
- **OBR_USE_REAL_FRESH_CHECKER** — Acceptance uses `lean4checker --fresh`. Use **OBR_FRESH_CHECK_CMD** for path. Build locally: `python scripts/setup/install_lean4checker.py` or `make install-lean4checker`.
- **OBR_WORKER_RUNNER** — `container` or `microvm` for isolated workers; default: local subprocess. See [architecture/worker-isolation.md](architecture/worker-isolation.md).
- **OBR_DOCKER_IMAGE** — Worker image (default `lean-worker:latest`). Build from `infra/docker/lean-worker.Dockerfile`.
- **OBR_CONTAINER_NETWORK** — Default `none`. Set `bridge` or `host` if runs need network (e.g. Lake).
- **OBR_CONTAINER_MEMORY_MB** / **OBR_CONTAINER_CPUS** — Resource limits for container runs.
- **OBR_INTERACTIVE_RUNNER_MAX** / **OBR_BATCH_RUNNER_MAX** — Max concurrent runs per runner kind (semaphore).
- **REVIEW_STORE** — `memory` (default) or `postgres`. For Postgres use **DATABASE_URL** and `pip install obligation-runtime-lean-gateway[postgres]`.
- **CHECKPOINTER** — In CLI, set to `postgres` for persistent checkpoints (resume across invocations). Requires `langgraph-checkpoint-postgres`.
- **OBR_POLICY_PACK** — Default policy pack (e.g. `strict_patch_gate_v1`, `reviewer_gated_execution_v1`).
- **OBR_CORS_ORIGINS** — Comma-separated allowed origins for the Review UI.
- **OBR_ENV** — Set to `production` to enforce Postgres and fail startup if not configured.
- **OBR_LOG_LEVEL** / **LOG_LEVEL** — Gateway log level. Logs are JSON with `request_id`.
- **OBR_METRICS_ENABLED** — When set, expose `GET /metrics` (Prometheus). Requires `[metrics]` extra.
- **OBR_REDIS_URL** / **REDIS_URL** — For distributed coordination when running multiple Gateway instances. Requires `[redis]` extra.

## Production state

Do not use in-memory state in production. Set `REVIEW_STORE=postgres`, `CHECKPOINTER=postgres`, and `DATABASE_URL`. When `OBR_ENV=production`, the Gateway fails startup if these are missing.

## Starting the Review UI

From `apps/review-ui`:

```bash
npm install
npm run dev
```

Set `NEXT_PUBLIC_GATEWAY_URL` to the Gateway URL. Review page: `http://localhost:3000/reviews/[threadId]`. Approve/reject via the UI; use **Resume run** (or `obr resume <thread_id>`) to continue the graph. Resume requires `CHECKPOINTER=postgres` and `DATABASE_URL`.

## Demos

Patch-verification demos require the Gateway to be running. From repo root: `make demo-core` (3 steps: good patch, sorry rejected, protected path) or `make demo-full` (6 steps: proof-preserving gate). See [demos/README.md](demos/README.md) and [demos/main-demo.md](demos/main-demo.md), [demos/full-demo.md](demos/full-demo.md). If the Gateway is not running, the demo scripts skip with exit 0.

## CLI (obr)

From repo root: `python -m obligation_runtime_orchestrator.cli <cmd>`. Commands: `open-environment`, `create-session`, `run-patch-obligation`, `run-protocol-obligation`, `review`, `resume`, `artifacts`, `regressions`. Use `--protected-paths`, `--policy-pack`, `--protocol-events-file` etc. as needed.

## Regressions

```bash
make test-regressions
# or
python -m obligation_runtime_orchestrator.cli regressions
```

Fixtures under `tests/regressions/fixtures/`. For LangSmith experiments: `make test-langsmith` (requires `LANGCHAIN_API_KEY`).

## Secrets

Never log `DATABASE_URL`, `LANGCHAIN_API_KEY`, or other secrets. Use env or a secret manager. The Gateway redacts known secret keys in logs.

## Logs and traces

- **Gateway:** Logs to stdout. Use a process manager or redirect.
- **Runtime:** When a tracer is configured, node events are emitted. Use `get_production_tracer()` from `obligation_runtime_telemetry.tracer` (OTLP or LangSmith via env). See `packages/telemetry/obligation_runtime_telemetry/README.md`.

## MCP server (stdio)

With the Gateway running:

```bash
OBLIGATION_GATEWAY_URL=http://localhost:8000 python -m obligation_runtime_orchestrator.mcp_server_main
```

Exposes obligation tools to MCP clients (e.g. Cursor). Session affinity is in-process.

## Resume from checkpoint

With in-memory checkpointer, state is per process. For cross-invocation resume (e.g. run in one shell, resume in another), set `CHECKPOINTER=postgres` and `DATABASE_URL`. After an interrupt for approval: approve/reject via UI or API, then resume with the same `thread_id`; the checkpointer restores graph position. CLI: `obr resume <thread_id> --decision approved`.

## Production checklist

- **Required:** `DATABASE_URL`, `REVIEW_STORE=postgres`, `CHECKPOINTER=postgres`, `OBR_CORS_ORIGINS` for UI.
- **DB:** Use managed or dedicated Postgres; backups and retention as per your runbook.
- **Scaling:** Gateway is stateless; run multiple instances behind a load balancer with shared Postgres. Set `OBR_CONTAINER_MEMORY_MB` and `OBR_CONTAINER_CPUS` for workers.
- **Rate limiting:** Not in Gateway; use reverse proxy or API gateway.
- **Incidents:** Use logs (`request_id`), `/health`, `/ready`, and traces to debug. Roll back by deploying a previous image.

## Backups and recovery

Back up Postgres (review store, checkpointer schema). Define retention and RTO/RPO in your runbook. Restore by pointing `DATABASE_URL` at the restored DB and redeploying the Gateway.

## Graceful shutdown

Send SIGTERM; uvicorn drains in-flight requests. Configure orchestrator wait (e.g. Kubernetes `terminationGracePeriodSeconds`). Use `/ready` so the load balancer stops routing before termination.

## Workers and containers

- **Local (default):** Commands run via subprocess on the host.
- **Container:** Set `OBR_WORKER_RUNNER=container`. Build: `docker build -f infra/docker/lean-worker.Dockerfile -t lean-worker:test .` Use **OBR_CONTAINER_MEMORY_MB** and **OBR_CONTAINER_CPUS** to limit resources. Default network is `none`; set **OBR_CONTAINER_NETWORK** to `bridge` or `host` if needed.
- **Leak check:** Containers are labeled `obr=1` and use `--rm`. After container-based runs, verify none remain: `docker ps -a --filter label=obr=1`. CI does this automatically.
- **Timeouts:** Build and runner timeouts (e.g. **OBR_BUILD_TIMEOUT**, **OBR_AXIOM_AUDIT_TIMEOUT**) are enforced; increase only when necessary.

## Running the full check

```bash
make install-dev-full
make check-full
```

See [tests-and-ci.md](tests-and-ci.md) for CI and optional jobs.

**See also:** [workflow.md](workflow.md), [deployment.md](deployment.md), [tests-and-ci.md](tests-and-ci.md), [architecture/gateway-api.md](architecture/gateway-api.md), [architecture/review-surface.md](architecture/review-surface.md).
