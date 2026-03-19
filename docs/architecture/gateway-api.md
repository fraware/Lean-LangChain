# Gateway API

Reference for the Lean Gateway HTTP API: endpoints, request/response, health, and OpenAPI. All routes are under the `/v1` prefix. Base URL is typically `http://localhost:8000` (configurable via `OBR_GATEWAY_URL`).

**Endpoints summary**

| Method + path | Purpose |
|---------------|---------|
| GET /health | Liveness probe. |
| GET /ready | Readiness probe. |
| GET /metrics | Prometheus metrics (when OBR_METRICS_ENABLED=1). |
| POST /v1/environments/open | Open environment; returns fingerprint_id. |
| POST /v1/sessions | Create session; returns session_id. |
| POST /v1/sessions/{id}/apply-patch | Apply patch in session. |
| POST /v1/sessions/{id}/interactive-check | Run interactive Lean check. |
| POST /v1/sessions/{id}/goal, /hover, /definition | LSP-backed goal/hover/definition. |
| POST /v1/sessions/{id}/batch-verify | Batch verify (final acceptance). |
| GET /v1/reviews/{thread_id} | Get review payload. |
| POST /v1/reviews/{thread_id}/approve, /reject | Submit approval decision. |
| POST /v1/reviews/{thread_id}/resume | Resume graph after approve/reject. |

## Health and readiness

- **GET /health** — Liveness probe; returns `200` and `{"status": "ok"}` when the process is running.
- **GET /ready** — Readiness probe. Returns `200` and `{"status": "ready"}` when the service accepts traffic. When `REVIEW_STORE=postgres`, the Gateway checks database connectivity; if Postgres is unreachable, returns `503` and `{"status": "not_ready", "reason": "database_unavailable"}`. Use for load balancer or Kubernetes readiness checks so unhealthy instances are removed from rotation.

CORS is configurable via `OBR_CORS_ORIGINS` (comma-separated origins). When set, the Gateway adds CORS middleware for those origins; when unset, no CORS headers are sent (same-origin only).

- **GET /metrics** — Prometheus text format (request count, latency histogram). Only registered when `OBR_METRICS_ENABLED=1` and the `prometheus_client` package is installed (e.g. `pip install obligation-runtime-lean-gateway[metrics]`). Use for alerting and dashboards.

## Endpoints

### Environment and sessions

- **POST /v1/environments/open** — Open an environment. Body: `repo_id`, optional `repo_path`, `repo_url`, `commit_sha` (default `HEAD`). Returns `fingerprint`, `fingerprint_id`, `snapshot_path`.
- **POST /v1/sessions** — Create a session. Body: `fingerprint_id`. Returns `session_id`, `fingerprint_id`, `workspace_path`.

### Session operations

- **POST /v1/sessions/{session_id}/apply-patch** — Apply a patch (dict of file path to content) to the session workspace.
- **POST /v1/sessions/{session_id}/interactive-check** — Run interactive check on a file. Body: `file_path`. Returns diagnostics, goals, `ok` (derived from diagnostics). Response includes `lsp_required: true` when LSP is not configured (full diagnostics/goals require OBR_USE_LEAN_LSP).
- **POST /v1/sessions/{session_id}/goal** — Get goal(s) at a position. Body: `file_path`, `line`, `column`. Uses LSP when `OBR_USE_LEAN_LSP` is set (`$/lean/plainGoal`, `$/lean/plainTermGoal`). Response includes `lsp_required: true` when LSP is not configured (goals empty).
- **POST /v1/sessions/{session_id}/hover** — Hover at position. Body: `file_path`, `line`, `column`. Response includes `lsp_required: true` when LSP is not configured.
- **POST /v1/sessions/{session_id}/definition** — Go to definition at position. Response includes `lsp_required: true` when LSP is not configured.
- **POST /v1/sessions/{session_id}/batch-verify** — Run batch verification (build, axiom audit, fresh check). Body: `target_files`, `target_declarations`. Returns `build`, `axiom_audit`, `fresh_checker`, `trust_level`, `ok`, `reasons`, and evidence-completeness flags `axiom_evidence_real`, `fresh_evidence_real` (boolean). Production requires real axiom and (when strict) real fresh; tests inject test doubles via conftest. When a test double is used, `axiom_audit.blocked_reasons` may include `axiom_audit_stub_unconfigured` and `axiom_evidence_real` is false; TypeScript SDK exports `AXIOM_AUDIT_NON_REAL_REASON` and `isNonRealAxiomAudit(response)` for detection (deprecated aliases `AXIOM_AUDIT_STUB_REASON` / `isStubAxiomAudit` remain).

### Reviews

- **GET /v1/reviews/{thread_id}** — Get review payload for a thread (when the graph has interrupted for approval).
- **POST /v1/reviews** — Create or update review (internal use).
- **POST /v1/reviews/{thread_id}/approve** — Submit approval decision.
- **POST /v1/reviews/{thread_id}/reject** — Submit rejection decision.
- **POST /v1/reviews/{thread_id}/resume** — Resume the graph after approve/reject; requires a decision already set and a checkpointer (CHECKPOINTER=postgres and DATABASE_URL, or in-process MemorySaver). Returns `{ ok, thread_id, status, artifacts_count }` or 503 if checkpointer/orchestrator unavailable.

## OpenAPI and client alignment

When the Gateway is running, OpenAPI docs: `http://localhost:8000/docs` (Swagger UI), `http://localhost:8000/redoc`, `http://localhost:8000/openapi.json`.

A checked-in snapshot lives at `contracts/openapi/lean-gateway.json` (`make export-openapi`). The **Python SDK** validates responses with Pydantic models derived from the same surface (`obligation_runtime_schemas.gateway_api`, `batch`, etc.). The **TypeScript SDK** (`@lean-langchain/sdk`) types are generated from that JSON (`packages/sdk-ts`: `npm run generate:types`). Monorepo `make check-full` runs **`verify-openapi-sdk-contract`** so the snapshot and generated TS file cannot drift without an intentional regen.

## Error handling

The API uses HTTP status codes and structured error responses. Stable error codes are documented in the Gateway module; see `obligation_runtime_lean_gateway.api.errors` for consistent error shapes.

**See also:** [workflow.md](../workflow.md), [runtime-graph.md](runtime-graph.md), [running.md](../running.md).
