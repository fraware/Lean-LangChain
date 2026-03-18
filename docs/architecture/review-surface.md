# Review surface

Human approval API and Review UI: when the graph returns `needs_review`, the run is interrupted and a review payload is pushed to the Gateway; a human approves or rejects, then **Resume run** continues the graph.

## API

- **GET /v1/reviews/{thread_id}** — Return the pending review payload for the thread (obligation summary, environment, patch metadata, diagnostics, axiom audit, batch summary, policy summary, reasons). 404 if no pending review.
- **POST /v1/reviews** — Create or replace a pending review (used by the orchestrator on interrupt). Payload must include `thread_id`.
- **POST /v1/reviews/{thread_id}/approve** — Record approval for the thread. 400 if no pending review.
- **POST /v1/reviews/{thread_id}/reject** — Record rejection for the thread. 400 if no pending review.
- **POST /v1/reviews/{thread_id}/resume** — Resume the graph after approve/reject. Requires a decision already set (call approve or reject first) and a checkpointer (`CHECKPOINTER=postgres` and `DATABASE_URL`, or in-process MemorySaver when orchestrator/langgraph are available). Returns `{ ok, thread_id, status, artifacts_count }`. 400 if no decision yet; 503 if no checkpointer or orchestrator/sdk not available.

See `docs/architecture/gateway-api.md` for full endpoint list.

## UI (Review UI)

The Review UI (`apps/review-ui`) is a Next.js app that:

- Loads the review payload for a thread via GET `/v1/reviews/{thread_id}`.
- Renders panels: **ObligationSummary**, **DiffPanel**, **DiagnosticsPanel**, **AxiomAuditPanel**, **PolicyDecisionPanel**, **ApprovalActions**.
- **ApprovalActions:** Approve and Reject buttons when status is `awaiting_review`. After the user approves or rejects, a **Resume run** button is shown; clicking it calls POST `/v1/reviews/{thread_id}/resume` so the graph continues from the checkpoint without running `obr resume` in the CLI.
- Set `NEXT_PUBLIC_GATEWAY_URL` to the Gateway base URL (e.g. `http://localhost:8000`). Review page: `http://localhost:3000/reviews/[threadId]`.

## Flow

1. Graph hits `interrupt_for_approval` and pushes payload to the Gateway (POST /v1/reviews).
2. User opens the Review UI for the thread_id, sees payload, and clicks Approve or Reject.
3. User clicks **Resume run** (or runs `obr resume <thread_id>`). The Gateway resume endpoint invokes the graph with the stored decision and checkpointer; the run completes (e.g. accepted or rejected).

For cross-process resume (e.g. run in one shell, approve in UI, resume in another), set `CHECKPOINTER=postgres` and `DATABASE_URL` so the graph state is shared.

## Webhooks

When `OBR_WEBHOOK_URL` is set, the gateway POSTs a JSON payload to that URL for lifecycle events. Delivery uses up to 2 retries with backoff (1s, 2s). Failures after retries are logged only.

**Payload shape:**
- **review.created** — After `POST /v1/reviews` creates a pending review. Body: `{ "event": "review.created", "thread_id": "<id>", "timestamp": "<ISO8601>", "payload": { ... } }`.
- **review.decision** — After approve or reject. Body: `{ "event": "review.decision", "thread_id": "<id>", "timestamp": "<ISO8601>", "decision": "approved" | "rejected" }`.
- **review.resumed** — After resume completes. Body: `{ "event": "review.resumed", "thread_id": "<id>", "timestamp": "<ISO8601>", "status": "<graph_status>", "artifacts_count": <n> }`.

**Signing (optional):** Set `OBR_WEBHOOK_SECRET`; the gateway sends `X-Webhook-Signature: sha256=<HMAC-SHA256(secret, body)>` so receivers can verify authenticity.

**Idempotency:** Each event includes `event`, `thread_id`, and `timestamp`. Receivers should deduplicate by `(event, thread_id)` or `(event, thread_id, timestamp)` and process at most once per logical event.

**See also:** [gateway-api.md](gateway-api.md), [runtime-graph.md](runtime-graph.md), [running.md](../running.md).
