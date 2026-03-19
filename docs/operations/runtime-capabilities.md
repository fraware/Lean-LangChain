# Runtime capabilities and degraded mode

Gateway and orchestrator expose machine-readable capability snapshots and **degraded reason codes** so operators can alert on partial stacks. Codes are defined in `packages/schemas/obligation_runtime_schemas/degraded_reasons.py` (`ALL_DEGRADED_REASON_CODES`).

## Gateway

**Endpoints:** `GET /health`, `GET /ready` (see gateway OpenAPI).

**Startup log:** `event=gateway_capabilities` with `degraded`, `caps`, and `reasons`.

| Environment | Effect |
|-------------|--------|
| `OBR_ENV=production` | Degraded flags are suppressed for capability listing; production still warns if Lean is unconfigured. |
| `OBR_USE_LEAN_LSP=1` | Lean interactive: real LSP. |
| `OBR_USE_REAL_LEAN=1` | Lean interactive: real subprocess. |
| `OBR_USE_REAL_AXIOM_AUDIT=1` | Axiom audit backend real. |
| `OBR_USE_REAL_FRESH_CHECKER=1` | Fresh checker real. |
| `REVIEW_STORE=postgres` + `REVIEW_STORE_POSTGRES_URI` or `DATABASE_URL` | Durable review store; otherwise in-memory. |

**Degraded reasons (non-production):**

| Code | Meaning |
|------|---------|
| `lean_interactive_unconfigured` | No LSP or real Lean flags set. |
| `axiom_audit_unconfigured` | Real axiom audit not enabled. |
| `fresh_checker_unconfigured` | Real fresh checker not enabled. |
| `review_store_memory` | Reviews stored in memory only. |

**Suggested alerts:** Fire when `degraded=true` in dev/staging; in production, alert on `lean_interactive=unconfigured` from logs.

## Orchestrator

**Endpoints:** `GET /health`, `GET /ready` on the orchestrator HTTP app (default port 8001).

**Startup log:** `event=orchestrator_capabilities` with `degraded`, `caps`, `reasons`.

| Environment | Effect |
|-------------|--------|
| `OBR_ENV=production` | Same degraded suppression pattern as gateway for listing. |
| `CHECKPOINTER=postgres` + `DATABASE_URL` | Postgres checkpointer when `langgraph.checkpoint.postgres` import succeeds. |
| (default) | In-memory checkpointer if available; else unavailable. |
| `OBR_GATEWAY_URL` | Gateway base URL for graph SDK calls (always non-empty default). |
| `OBR_POLICY_PACK` | Pack name or path; if load fails, non-production health reports `policy_pack_unresolved`. |
| `OBR_ORCHESTRATOR_READY_FAIL_ON_DEGRADED=1` | `GET /ready` returns 503 when capabilities are degraded. |

**Degraded reasons (non-production):**

| Code | Meaning |
|------|---------|
| `checkpointer_memory` | Using memory checkpointer. |
| `checkpointer_unavailable` | No checkpointer implementation importable. |
| `langgraph_unavailable` | `langgraph` not installed. |
| `policy_pack_unresolved` | `OBR_POLICY_PACK` (or default) does not load. |

**Suggested alerts:** Non-production: `degraded=true`. Production: warn if `checkpointer=memory` (startup log). For resume flows, alert on `GET /ready` 503 with `checkpointer_unavailable`.

## See also

- [integrate.md](../integrate.md) — wiring gateway and orchestrator.
- [tests-and-ci.md](../tests-and-ci.md) — CI gates.
