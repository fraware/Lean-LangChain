# Deployment guide

How to deploy the Gateway and optional Review UI in production. For day-to-day running and environment variables, see [running.md](running.md).

## Principles

- **Stateless Gateway** — Use Postgres for review store and checkpoints so instances can scale and survive restarts.
- **Health and readiness** — Use `/health` and `/ready`; when using Postgres, `/ready` checks the database.
- **Secrets** — Never commit `.env`; use env or a secret manager. Set `DATABASE_URL`, and optionally `LANGCHAIN_API_KEY` or `OBR_OTLP_ENDPOINT` for tracing.
- **Containers** — Run Gateway (and workers) in containers with health checks and resource limits.

## Prerequisites

- Docker and Docker Compose (or Kubernetes).
- Postgres; optional Lean 4 and lean4checker for full verification.

## 1. Clone and build

Clone the repository (replace `<owner>` with your GitHub org or username):

```bash
git clone https://github.com/<owner>/lean-langchain.git
cd lean-langchain
```

Then build from the repo root:

```bash
# Gateway (required)
docker build -f infra/docker/gateway.Dockerfile -t obligation-gateway:latest .

# Review UI (optional)
docker build -f infra/docker/review-ui.Dockerfile -t obligation-review-ui:latest .
```

## 2. Configure

Copy `.env.example` to `.env` and set at least:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres connection string. |
| `REVIEW_STORE=postgres` | Use Postgres for review state. |
| `CHECKPOINTER=postgres` | Use Postgres for checkpoints (resume). |
| `OBR_USE_REAL_LEAN` or `OBR_USE_LEAN_LSP` | Required for the Gateway. |
| `OBR_USE_REAL_AXIOM_AUDIT` | Required for batch verification. |
| `OBR_ENV=production` | Enforces the above and fails startup if missing. |

See [running.md](running.md) for the full list of environment variables.

## 3. Deploy

**Docker Compose:**

```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

Use an env file (e.g. `.env.production`) with the required variables. Do not commit secrets.

**Kubernetes:** Deploy the Gateway as a Deployment with liveness (`GET /health`) and readiness (`GET /ready`) probes. Use Secrets for `DATABASE_URL` and ConfigMaps for other env. Expose via Service and Ingress; put TLS and rate limiting at the ingress.

## 4. Verify

```bash
curl -s http://localhost:8000/health   # 200
curl -s http://localhost:8000/ready   # 200 when DB is up; 503 if not
```

Then run a smoke request (e.g. create a session or call batch-verify).

## 5. Review UI (optional)

The Review UI needs the Gateway URL at **build time**: set `NEXT_PUBLIC_GATEWAY_URL` when building. Run the container with the same variable at runtime if needed. See [running.md](running.md) for starting the UI locally.

## Rollback and backups

- **Rollback:** Redeploy a previous image tag. Postgres state is backward-compatible.
- **Backups:** Back up Postgres (e.g. `pg_dump` or managed-DB snapshots). Document retention in your runbook.

## Graceful shutdown

Send SIGTERM to the Gateway process; uvicorn drains in-flight requests. Configure your orchestrator (e.g. Kubernetes `terminationGracePeriodSeconds`) to wait long enough. Use readiness so the load balancer stops routing before termination.

**See also:** [running.md](running.md), [architecture/gateway-api.md](architecture/gateway-api.md), [SECURITY.md](../SECURITY.md).
