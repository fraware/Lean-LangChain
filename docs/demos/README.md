# Demo scenarios

Reproducible scenarios for patch verification and for protocol (multi-agent) rules. Use these to see how the runtime accepts good patches, rejects bad ones, and pauses for human review when configured.

**Examples vs demos:** Minimal SDK usage (open env, session, batch-verify only) is in **examples/** ([minimal_sdk_gateway.py](../examples/minimal_sdk_gateway.py)). The **demos** here are full flows run via the CLI (`obr` / `make demo-*`) and scripts in **scripts/demos/**.

**Before you start:** Run the Gateway from the repo root (`uvicorn lean_langchain_gateway.api.app:app`). If it is not at `http://localhost:8000`, set `OBR_GATEWAY_URL`. Run the CLI from the repo root as `python -m lean_langchain_orchestrator.cli` (or `obr` if installed).

**When demos skip:** The core demo, full demo, and scenarios 1–4 require a running Gateway. If the Gateway is not reachable (or fixtures are missing), their scripts exit with code 0 and print a skip message to stderr. Scenario 5 (reviewer gated) runs without the Gateway and always executes.

---

## Scenarios overview

| # | What it shows | What you run | Result |
|---|----------------|--------------|--------|
| 1 | Good patch accepted | `obr open-environment` → `create-session` → `run-patch-obligation` | `status: accepted`, at least one evidence bundle |
| 2 | Bad patch (e.g. `sorry`) rejected | Same flow with `--patch-file` pointing at a sorry fixture | `status: rejected` or `failed` |
| 3 | Protected path → human review → resume | Same flow with a protected path; finish in Review UI or with `obr resume` | Run pauses; after Approve + **Resume run**: `accepted` |
| 4 | Interactive passes, batch fails | Patch that passes per-file check but fails full verification | `status: rejected` |
| 5 | Reviewer required but no approval | Protocol check that requires an approval event; you send events without one | `decision: blocked`, reason `missing_approval_token` |

---

## Main demo (recommended first)

The most useful end-to-end path is: good patch accepted, bad patch rejected, then protected path with human review and resume. That flow is documented in **[main-demo.md](main-demo.md)**.

- **`make demo-core`** — Runs scenarios 1–3 in order. Scenario 3 uses CLI resume when `CHECKPOINTER=postgres` and `DATABASE_URL` are set; otherwise step 3 is skipped. Exits successfully if the Gateway is down or fixtures are missing.
- **`make demo-core-ui`** — Runs 1 and 2, then 3 up to the pause; prints the Review UI URL so you can Approve and click **Resume run** in the browser.

### Full demo

Proof-preserving patch gate: valid proof edit accepted, sorry and false theorem rejected, protected path with approve/reject, evidence bundle export. See **[full-demo.md](full-demo.md)**.

- **`make demo-full`** — Runs all 6 steps (steps 5–6 require Postgres).
- **`make demo-full-ui`** — Runs steps 1–4, then step 5a up to the pause; prints the Review UI URL for manual approve/reject and resume.

---

## Scenario 1: Good patch → accepted

Open an environment, create a session, run the patch flow with no patch or a trivial patch. You should get `accepted` and at least one evidence bundle.

```bash
obr open-environment --repo-id lean-mini --repo-path tests/integration/fixtures/lean-mini
# Use fingerprint_id from the output:
obr create-session <fingerprint_id>
obr run-patch-obligation --repo-id lean-mini --repo-path tests/integration/fixtures/lean-mini
```

Expected: `"status": "accepted"`, `artifacts_count` >= 1.

---

## Scenario 2: Patch with `sorry` → rejected

When the patch introduces `sorry` or verification fails, the run ends with `rejected` or `failed`.

Use the same flow as scenario 1 but pass a patch that introduces `sorry` (e.g. `scripts/fixtures/sorry_patch.lean`) with `--patch-file` and `--patch-apply-path` so it applies to the right file (e.g. `Mini/Basic.lean`). Expected: `rejected` or `failed`.

Automation: `make demo-scenario-2` runs this against the Gateway.

---

## Scenario 3: Protected path → review required

When the patch touches a path that is protected by policy, the run is paused for human review. The review payload is sent to the Gateway.

**Resuming the run**

- **Same process:** Tests and in-process scripts can run the graph twice with the same `thread_id` and an in-memory checkpointer: first run stops at “awaiting approval”, second run passes the approval decision and continues. No Postgres needed.
- **CLI then UI (or CLI again):** To run `obr run-patch-obligation` in one terminal and later `obr resume <thread_id>` in another (or use the Review UI’s **Resume run**), state must be shared. Set `CHECKPOINTER=postgres` and `DATABASE_URL` so both the Gateway and the CLI use the same stored state. Without Postgres, in-memory state is per process and resume in a second run will not see the paused state.

Inspect the review: `obr review <thread_id>` (payload with `status: "awaiting_review"`). Then approve or reject via the Review UI (or POST to `/v1/reviews/<thread_id>/approve` or `/reject`), and click **Resume run** in the UI (or POST to `/v1/reviews/<thread_id>/resume`, or `obr resume <thread_id>`).

---

## Scenario 4: Interactive passes, batch fails → rejected

If the per-file check passes but full verification fails (e.g. build or fresh checker), the run is rejected. You get `status: rejected`; reasons may include `batch_verify_failed`, `lake_build_failed`, or `fresh_checker_failed`.

---

## Scenario 5: Reviewer required but no approval → blocked

Some protocol rules require an approval event. If you run the “reviewer gated” check with events that do not include approval, the result is blocked.

```bash
obr run-protocol-obligation --obligation-class reviewer_gated --pack reviewer_gated_execution_v1 --events-file events.json
```

Expected: `decision: blocked`, reasons include `missing_approval_token`. Automation: `make demo-scenario-5` or `python scripts/demos/run_demo_scenario_5.py`.

---

## Protocol demos: handoff and lock

Beyond patch verification, the runtime can evaluate **protocol** rules (e.g. who can hand off work, who holds a lock).

### Handoff (same owner / delegate)

Checks that a “delegate” event is allowed given prior “claim” events (e.g. same owner). Supply events in a JSON file and run:

```bash
echo '[{"kind":"claim","event_id":"e1","actor":{"agent_id":"alice","role":"owner"},"task":{"task_id":"t1","task_class":"patch"}},{"kind":"delegate","event_id":"e2","actor":{"agent_id":"alice","role":"owner"},"task":{"task_id":"t1","task_class":"patch"},"prior_event_ids":["e1"]}]' > events.json
obr run-protocol-obligation --obligation-class handoff_legality --pack single_owner_handoff_v1 --events-file events.json
```

Expected: `decision: "accepted"`. For a different owner (e.g. `actor.agent_id: "bob"` in the delegate event), expected: `decision: "rejected"`, `reasons: ["owner_mismatch"]`.

### Lock ownership

Checks that only one agent holds a lock and that only the holder can release it. Use obligation class `lock_ownership_invariant` and pack `lock_ownership_invariant_v1`. Events use `kind: "lock"` and `kind: "release"` with `actor.agent_id`. Conflicting lock (e.g. lock by B while A holds) gives `reasons: ["lock_conflict"]`; release without a prior lock gives `reasons: ["release_without_lock"]`.

```bash
obr run-protocol-obligation --obligation-class lock_ownership_invariant --pack lock_ownership_invariant_v1 --events-file lock_events.json
```

---

## Running regressions

```bash
obr regressions
```

Runs the regression suite under `tests/regressions/`. Cases are loaded from `packages/evals/lean_langchain_evals/fixtures.py` and from JSON in `tests/regressions/fixtures/` (e.g. `multi_agent_handoff_good.json`, `patch_sorry_case.json`). Reason codes and expected decisions are defined in `packages/policy/lean_langchain_policy/constants.py`.

---

**See also:** [workflow.md](../workflow.md), [main-demo.md](main-demo.md), [full-demo.md](full-demo.md), [running.md](../running.md).
