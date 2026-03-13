# Infra

**Purpose:** Gateway container, Review UI container, Docker Compose, worker isolation (container/microVM), and persistence (Postgres). **Audience:** operators and deployers.

## Gateway container

- **Dockerfile:** `infra/docker/gateway.Dockerfile` — multi-stage build, non-root user, HEALTHCHECK using `/health`. Build from repo root: `docker build -f infra/docker/gateway.Dockerfile -t obligation-gateway:latest .`
- **Compose:** `infra/docker/docker-compose.yml` — Gateway + Postgres; run from repo root: `docker compose -f infra/docker/docker-compose.yml up -d`. Set `OBR_CORS_ORIGINS`, `DATABASE_URL`, `REVIEW_STORE=postgres`, `CHECKPOINTER=postgres` for production-style runs. When `REVIEW_STORE=postgres`, `GET /ready` checks DB connectivity and returns 503 if the database is unreachable. See **docs/running.md** and **docs/deployment.md**.

## Review UI container

- **Dockerfile:** `infra/docker/review-ui.Dockerfile` — multi-stage Next.js build with `output: "standalone"`, non-root user. Build from repo root with Gateway URL at build time: `docker build --build-arg NEXT_PUBLIC_GATEWAY_URL=https://gateway.example.com -f infra/docker/review-ui.Dockerfile -t obligation-review-ui:latest .` Run with `docker run -p 3000:3000 obligation-review-ui:latest`. See **docs/deployment.md** and **apps/review-ui/README.md**.

## Worker isolation (container and microVM runner)

The gateway supports optional **container** and **microVM** runners so Lean execution runs in an isolated environment with the workspace mounted.

- **Runner abstraction:** `LeanRunner` protocol in `apps/lean-gateway/.../server/runner.py`. `LocalRunner` runs commands via subprocess on the host (default). `ContainerRunner` runs `docker run -v <workspace>:/workspace -w /workspace <image> <command>`. `MicroVMRunner` (runsc) runs the same with `--runtime=runsc`; `FirecrackerRunner` delegates to an external script.
- **Container:** Set `OBR_WORKER_RUNNER=container`. Optionally set `OBR_DOCKER_IMAGE` (default: `lean-worker:latest`).
- **MicroVM (runsc):** Set `OBR_WORKER_RUNNER=microvm` and ensure Docker is configured with the gVisor runsc runtime. Uses `OBR_DOCKER_IMAGE` or `OBR_MICROVM_IMAGE`. Same image as container.
- **MicroVM (Firecracker):** Set `OBR_WORKER_RUNNER=microvm`, `OBR_MICROVM_RUNTIME=firecracker`, and `OBR_MICROVM_FIRECRACKER_RUN` to the path of a script that runs the command in a Firecracker microVM and prints JSON `{stdout, stderr, returncode}`.
- **Image:** The default `infra/docker/lean-worker.Dockerfile` uses the Lean 4 base image (`leanprovercommunity/lean4`), so `lake` and `lean` are in PATH. Build from repo root: `docker build -f infra/docker/lean-worker.Dockerfile -t lean-worker:test .` (or `lean-worker-lean4.Dockerfile` for the same result). For a minimal Python-only image without Lean, use `infra/docker/lean-worker-slim.Dockerfile`. The entrypoint runs the command passed as arguments (e.g. `lake build`, `lean4checker --fresh`).
- **CI / local:** Omit `OBR_WORKER_RUNNER` or set it to anything other than `container` or `microvm` to use `LocalRunner`.

See `docs/running.md` for environment variables.

## Persistence (Postgres)

- **Review store:** Set `REVIEW_STORE=postgres` and `DATABASE_URL` (or `REVIEW_STORE_POSTGRES_URI`). Table `obr_reviews` is created automatically. Install gateway with `[postgres]` extra for `psycopg`.
- **Checkpointer:** In the orchestrator, set `CHECKPOINTER=postgres` and `DATABASE_URL` to persist LangGraph state. Install `langgraph-checkpoint-postgres`; run `.setup()` on first use (CLI does this). Optional Redis for queues is future work.

**See also:** [docs/running.md](../docs/running.md), [docs/deployment.md](../docs/deployment.md), [docs/architecture/worker-isolation.md](../docs/architecture/worker-isolation.md).
