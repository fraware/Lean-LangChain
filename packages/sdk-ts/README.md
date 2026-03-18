# obligation-runtime-sdk-ts

TypeScript/JavaScript client for the [Obligation Runtime](https://github.com/leanprover/Lean-LangChain) Gateway API. Use it to call a running Lean Gateway from Node.js or the browser (open environment, create session, apply patch, interactive check, batch verify, review, resume).

## Install

```bash
npm install obligation-runtime-sdk-ts
```

From the monorepo (development):

```bash
cd packages/sdk-ts && npm install && npm run build
```

## Usage

```typescript
import { ObligationRuntimeClient } from "obligation-runtime-sdk-ts";

const client = new ObligationRuntimeClient("http://localhost:8000");

// Open environment and create session
const env = await client.openEnvironment({ repo_id: "my-repo" });
const session = await client.createSession({ fingerprint_id: env.fingerprint_id });

// Apply patch and run checks
await client.applyPatch(session.session_id, { files: { "Main.lean": "def x := 1" } });
const check = await client.interactiveCheck(session.session_id, { file_path: "Main.lean" });
const batch = await client.batchVerify(session.session_id, {
  target_files: ["Main.lean"],
  target_declarations: [],
});

// Review flow (when the graph interrupts for human approval)
const payload = await client.getReviewPayload(threadId);
await client.submitReviewDecision(threadId, "approve");
await client.resume(threadId);
```

## API

- `openEnvironment(payload)` — open environment by repo_id / repo_path / repo_url / commit_sha
- `createSession(payload)` — create session for a fingerprint_id
- `applyPatch(sessionId, payload)` — apply files to session
- `interactiveCheck(sessionId, payload)` — run interactive check (file_path)
- `getGoal(sessionId, payload)` — get goal at line/column (file_path, line, column)
- `hover(sessionId, payload)` — hover at position (file_path, line, column)
- `definition(sessionId, payload)` — definition at position (file_path, line, column)
- `batchVerify(sessionId, payload)` — batch verify (target_files, target_declarations)
- `getReviewPayload(threadId)` — get pending review payload
- `createPendingReview(payload)` — create/replace pending review (thread_id required)
- `submitReviewDecision(threadId, decision)` — approve or reject (decision: `"approve"` | `"reject"`)
- `resume(threadId)` — resume graph after approve/reject (requires checkpointer and OBR_ORCHESTRATOR_URL on gateway)

Errors are thrown as `ObligationRuntimeError` with `code`, `message`, `statusCode`, and optional `requestId` / `details`. Use `isApiError(body)` to detect API error responses.

## Versioning

This package follows the same version as the Obligation Runtime repo. Pre-1.0 versions may change the API; prefer pinning the minor version.
