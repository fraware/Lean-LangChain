# Full demo: proof-preserving patch gate

This demo shows Lean as the semantic authority: valid proof edits are accepted, admitted proofs (`sorry`) and false theorems are rejected, and protected paths require human approve or reject. Every accepted run can produce an evidence bundle for audit.

**What you'll see**

1. **No patch (baseline)** — Run with no patch; verification passes; status `accepted`, evidence bundle.
2. **Valid proof edit** — Patch that changes the proof tactic (e.g. `simp` to `rfl`) but keeps the theorem correct; status `accepted`.
3. **Sorry patch** — Patch that introduces `sorry`; status `rejected` or `failed`.
4. **False theorem** — Patch that changes the theorem statement to something false so the proof no longer typechecks; build fails; status `rejected` or `failed`.
5. **Protected path, approve** — Run that touches a protected path; paused for review; you approve and resume; status `accepted`.
6. **Protected path, reject** — Same as 5 but you reject; after resume, status `rejected`.
7. **Evidence bundle** — Export artifacts for the approved run; file contains witness bundle (environment, batch result, policy, approval).

---

## Run the demo

With the Gateway running (see [Prerequisites](#prerequisites)). If the Gateway is not running, the script skips with exit 0 and prints a message to stderr.

```bash
make demo-full
```

This runs all six steps. Steps 5a, 5b, and 6 require `CHECKPOINTER=postgres` and `DATABASE_URL`; if not set, steps 1–4 run and the script exits 0 with a skip message.

To complete step 5a in the browser (approve then resume) instead of CLI resume:

```bash
make demo-full-ui
```

Then open the URL printed by the script, click **Approve** (or **Reject** for the reject path), then **Resume run**.

For more control: `python scripts/demos/run_full_demo.py --help` (e.g. `-v` for verbose).

---

## Flow

```
Step 1 (no patch)     → accepted
Step 2 (valid edit)   → accepted
Step 3 (sorry)        → rejected
Step 4 (false theorem)→ rejected (build fails)
Step 5a (protected)  → awaiting_approval → Approve → Resume → accepted
Step 5b (protected)  → awaiting_approval → Reject  → Resume → rejected
Step 6               → obr artifacts → full_demo_witness.json
```

---

## Prerequisites

- **Gateway** running. From the repo root:
  ```bash
  uvicorn obligation_runtime_lean_gateway.api.app:app --reload
  ```
  If the Gateway is not on `http://localhost:8000`, set `OBR_GATEWAY_URL`.

- **Steps 5–6:** Set **`CHECKPOINTER=postgres`** and **`DATABASE_URL`** for both the process that starts the Gateway and the process that runs the CLI. For "Resume run" in the browser, start the Review UI from `apps/review-ui`: `npm install && npm run dev`, with `NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000`. Details: [running.md](../running.md).

---

## Fixtures

| File | Description |
|------|-------------|
| `scripts/fixtures/valid_proof_edit_patch.lean` | Full content for `Mini/Basic.lean` with proof `by rfl` (still correct). |
| `scripts/fixtures/false_theorem_patch.lean` | Theorem statement changed to false (`n + 0 = 0`); proof `by simp` fails. |
| `scripts/fixtures/sorry_patch.lean` | Theorem body replaced with `sorry` (admitted proof). |

---

## Evidence bundle

After an accepted run that went through review (e.g. step 5a), export the evidence bundle:

```bash
obr artifacts --thread-id full-demo-5a --output witness.json
```

The file contains the list of artifacts; each accepted run appends a `witness_bundle` with environment fingerprint, batch result, policy decision, and approval payload. See [core-primitives.md](../architecture/core-primitives.md) and [glossary.md](../glossary.md) for WitnessBundle and related terms.

The demo script writes `full_demo_witness.json` in the repo root when step 6 runs.

---

## Troubleshooting

| What you see | Likely cause | What to do |
|--------------|---------------|------------|
| Script exits with "Skipped: Gateway not running or open-environment failed" | Gateway not running or wrong URL | Start the Gateway; set `OBR_GATEWAY_URL` if not `http://localhost:8000`. |
| "Skipped: steps 5-6 require CHECKPOINTER=postgres and DATABASE_URL" | No shared state for resume/artifacts | Set `CHECKPOINTER=postgres` and `DATABASE_URL` for both Gateway and CLI. |
| "Resume run" in the UI returns 503 or does nothing | Gateway not using Postgres for state | Start the Gateway with `CHECKPOINTER=postgres` and `DATABASE_URL`. |
| Step 2 or 4 expected rejected but got accepted | Patch not applied or wrong paths | Fixture repo must be `tests/integration/fixtures/lean-mini`; `--patch-apply-path Mini/Basic.lean`, `--target-files Mini/Basic.lean`. |
| Step 6 failed: no witness_bundle | Artifacts exported before an accepted run with that thread_id | Step 6 uses thread_id `full-demo-5a`; ensure step 5a completed and was approved. |

**See also:** [main-demo.md](main-demo.md), [README.md](README.md), [workflow.md](../workflow.md), [running.md](../running.md).
