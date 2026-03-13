# Main demo: verification and human review

This demo walks through the most important path in the Obligation Runtime: verifying a Lean patch, seeing a bad patch rejected, and then going through human approval when the change touches protected code.

**What you’ll see**

1. **Good patch** — Verification passes; run is accepted and you get an evidence bundle.
2. **Bad patch** — A patch that introduces `sorry` (or breaks the build) is rejected.
3. **Protected file** — A patch that touches a protected path is paused for human review; you approve in the Review UI and resume the run to completion.

---

## Run the demo

With the Gateway running (see [Prerequisites](#prerequisites)). If the Gateway is not running, the script skips with exit 0 and prints a message to stderr.

```bash
make demo-core
```

This runs all three steps. Step 3 uses the CLI to resume when Postgres is configured. To finish step 3 in the browser instead:

```bash
make demo-core-ui
```

Then open the URL printed by the script, click **Approve**, then **Resume run**.

For more control: `python scripts/demos/run_core_demo.py --help` (e.g. `-v` for verbose output).

---

## Flow

```
Good patch  →  accepted + evidence bundle
Bad patch   →  rejected or failed
Protected   →  paused for review  →  Approve in UI  →  Resume  →  accepted
```

1. **Step 1 — Good patch:** No patch or a trivial patch; verification passes; run ends with `accepted` and at least one evidence bundle.
2. **Step 2 — Bad patch:** Patch that introduces `sorry` or fails verification; run ends with `rejected` or `failed`.
3. **Step 3 — Protected path:** Patch touches a protected path; run is paused for human review. You open the Review UI, approve (or reject), then click **Resume run** so the run finishes (e.g. `accepted` if you approved).

---

## What this shows

- **Lean decides acceptance.** Acceptance is based on Lean (build, axiom audit, fresh checker), not on ad‑hoc tests.
- **Batch verification is the authority.** The final accept/reject decision comes from batch verification (build + axiom audit + fresh checker). The per‑file interactive check is for feedback only.
- **Policy can require human review.** When the patch touches protected paths, the run is paused and a human must approve or reject in the Review UI.
- **Resume from the UI.** After you approve or reject, you click **Resume run** (or call the resume API); the run continues from where it stopped and then finishes.
- **Evidence bundle.** Every accepted run can produce an evidence bundle (environment, verification results, policy decision, and approval if there was a review). With strict mode enabled, acceptance also requires real axiom and fresh-checker evidence.

---

## Prerequisites

- **Gateway** running. From the repo root:
  ```bash
  uvicorn obligation_runtime_lean_gateway.api.app:app --reload
  ```
  If the Gateway is not on `http://localhost:8000`, set `OBR_GATEWAY_URL`.

- **Step 3 in the Review UI:** So that “Resume run” in the browser works, the CLI and the Gateway must share the same stored state. Set **`CHECKPOINTER=postgres`** and **`DATABASE_URL`** for both the process that starts the Gateway and the process that runs the CLI. Start the Review UI from `apps/review-ui`: `npm install && npm run dev`, with `NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000`. Details: [running.md](../running.md).

---

## Step-by-step commands

### Step 1: Good patch → accepted

Open an environment, create a session, and run the patch flow with no patch (or a trivial patch). You should see status `accepted` and at least one evidence bundle.

```bash
obr open-environment --repo-id lean-mini --repo-path tests/integration/fixtures/lean-mini
# Use the fingerprint_id from the output:
obr create-session <fingerprint_id>
obr run-patch-obligation --repo-id lean-mini --repo-path tests/integration/fixtures/lean-mini
```

Expected: `"status": "accepted"`, `artifacts_count` >= 1.

Example output:

```json
{
  "status": "accepted",
  "artifacts_count": 1
}
```

### Step 2: Bad patch → rejected

Same flow, but use a patch that introduces `sorry` or fails verification. The run should end with `rejected` or `failed`.

```bash
obr open-environment --repo-id lean-mini --repo-path tests/integration/fixtures/lean-mini
obr create-session <fingerprint_id>
obr run-patch-obligation --repo-id lean-mini --repo-path tests/integration/fixtures/lean-mini \
  --patch-file scripts/fixtures/sorry_patch.lean \
  --patch-apply-path Mini/Basic.lean \
  --target-files Mini/Basic.lean
```

Expected: `"status": "rejected"` or `"failed"`.

### Step 3: Protected path → review in UI → resume → accepted

Run the patch flow with a protected path so the run is paused for review. Then complete it via the Review UI (or `obr resume`).

```bash
obr open-environment --repo-id lean-mini --repo-path tests/integration/fixtures/lean-mini
obr create-session <fingerprint_id>
obr run-patch-obligation --repo-id lean-mini --repo-path tests/integration/fixtures/lean-mini \
  --thread-id core-demo-3 \
  --protected-paths Mini/Basic.lean
```

Expected: run stops with `"status": "awaiting_approval"`. Then:

1. Open **http://localhost:3000/reviews/core-demo-3** in the Review UI.
2. Click **Approve** (or Reject).
3. Click **Resume run**. The run continues and completes (e.g. `accepted` if you approved).

From the CLI instead: `obr resume core-demo-3 --decision approved` (same Postgres checkpointer must be used so the CLI and Gateway share state).

---

## Where to look in the repo

| Topic | Where | Notes |
|-------|--------|------|
| **Strict verification** | [apps/lean-gateway/.../batch/combine.py](../../apps/lean-gateway/obligation_runtime_lean_gateway/batch/combine.py), [acceptance-lane.md](../architecture/acceptance-lane.md) | With strict mode, acceptance requires real axiom audit and fresh checker. |
| **Review UI and resume** | [routes_reviews.py](../../apps/lean-gateway/obligation_runtime_lean_gateway/api/routes_reviews.py), [apps/review-ui](../../apps/review-ui) | Policy says “needs review” → run pauses → approve/reject in UI → resume. |
| **Evidence bundle** | [core-primitives.md](../architecture/core-primitives.md), [glossary.md](../glossary.md), `obr artifacts` | Accepted runs can produce a full evidence bundle for audit. |
| **Verification graph** | [runtime/graph.py](../../apps/orchestrator/obligation_runtime_orchestrator/runtime/graph.py) | Flow: init → interactive check → batch verify → policy → pause for review or finalize. |
| **Protocol packs** | [demos/README.md](README.md) | Packs for reviewer-gated runs, handoff, and lock ownership. |

---

## Strict verification (real axiom and fresh evidence)

To require **real** axiom and fresh-checker evidence (not test doubles), set:

- `OBR_ACCEPTANCE_STRICT=1`
- `OBR_USE_REAL_AXIOM_AUDIT=1` and `OBR_AXIOM_AUDIT_CMD` to a script that runs your axiom producer (e.g. `lake exe axiom_list`)
- `OBR_USE_REAL_FRESH_CHECKER=1` and `lean4checker` (or `OBR_FRESH_CHECK_CMD`) on PATH

Then batch verification returns `ok: false` and `trust_level: blocked` unless both axiom and fresh evidence are real. See [running.md](../running.md) and [tests-and-ci.md](../tests-and-ci.md).

---

## Exporting the evidence bundle

After an accepted run, export the evidence bundles for that run:

```bash
obr artifacts --thread-id <thread_id> --output witness.json
```

The file includes environment fingerprint, interactive and batch results (with evidence flags), policy decision, and approval data if the run went through review. Use the same `thread_id` as for `run-patch-obligation` (e.g. `core-demo-3` for step 3). Requires a checkpointer (Postgres or in-process). See `obr artifacts --help`.

---

## Commands summary

| Command | Effect |
|--------|--------|
| `make demo-core` | Run all three steps (step 3 uses CLI resume when Postgres is set). Exits successfully even if Gateway is down or fixtures are missing (demo is skipped). |
| `make demo-core-ui` | Run steps 1 and 2, then step 3 up to the pause; print the Review UI URL and tell you to Approve and click **Resume run**. |
| `python scripts/demos/run_core_demo.py -v` | Same as `demo-core` with verbose logging. |

More scenarios and regression commands: [README.md](README.md).

---

## Troubleshooting

| What you see | Likely cause | What to do |
|--------------|--------------|------------|
| Script exits with “Skipped: Gateway not running or open-environment failed” | Gateway not running or wrong URL | Start the Gateway; set `OBR_GATEWAY_URL` if not using `http://localhost:8000`. |
| “Skipped: scenario 3 with CLI resume requires CHECKPOINTER=postgres and DATABASE_URL” | No shared state for resume | Set `CHECKPOINTER=postgres` and `DATABASE_URL` for both the Gateway and the CLI. |
| “Resume run” in the UI returns 503 or does nothing | Gateway not using Postgres for state | Start the Gateway with `CHECKPOINTER=postgres` and `DATABASE_URL`. |
| “invalid JSON” or “empty stdout” from run-patch-obligation | Gateway returned HTML (e.g. 502) or non-JSON | Run with `-v` to inspect output; ensure the Gateway is up and the request reaches it. |
| Step 2 expected rejected but got accepted | Sorry patch not applied or wrong paths | Use `--patch-apply-path Mini/Basic.lean` and `--target-files Mini/Basic.lean`; fixture repo: `tests/integration/fixtures/lean-mini`. |

For a longer narrative that includes valid proof edits, false-theorem rejection, human reject path, and evidence export, see [full-demo.md](full-demo.md).

**See also:** [README.md](README.md), [workflow.md](../workflow.md), [running.md](../running.md).
