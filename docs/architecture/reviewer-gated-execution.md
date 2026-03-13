# Reviewer-gated execution

When an approval token is required, how it is supplied, and where it is enforced. Constants: `packages/policy/obligation_runtime_policy/constants.py` (e.g. `REASON_MISSING_APPROVAL_TOKEN`, `DECISION_BLOCKED`).

## Contract

1. **When is an approval token required?**  
   When the policy pack in use has `reviewer_gated_execution: true` (e.g. pack `reviewer_gated_execution_v1`), the runtime requires an approval token before policy_review can yield `accepted`. Without a token, policy_review returns `decision: blocked` with reason `missing_approval_token`.

2. **How is the approval token supplied?**  
   The approval token is represented by the state field `approval_decision`:
   - `approved`: execution is allowed to proceed (e.g. to finalize with accepted).
   - `rejected`: execution is terminated (rejected).
   - `pending` or unset: when the pack is reviewer-gated, treated as missing token; policy_review returns blocked.

   The token is set in one of two ways:
   - **Interrupt and resume:** The graph interrupts at `interrupt_for_approval` when policy returns `needs_review`. The operator (or API) performs a review; on resume, the resume payload sets `approval_decision` to `approved` or `rejected`. That value is the approval token for the rest of the run.
   - **Pre-set (testing / automation):** Initial state can set `approval_decision` to `approved` or `rejected` so that reviewer-gated packs do not block (e.g. for tests or when approval was obtained out-of-band).

3. **Where is the check enforced?**  
   In the patch-admissibility graph, the check is enforced in the `policy_review` node: after loading the pack (from state `policy_pack_name` or env `OBR_POLICY_PACK`), if `pack.reviewer_gated_execution` is true and `state.approval_decision` is not in `("approved", "rejected")`, the node returns `policy_decision.decision = "blocked"` and `reasons = ["missing_approval_token"]` and does not run the normal patch policy evaluation.

4. **CLI, API, and state.**  
   - `obr run-patch-obligation` accepts `--policy-pack`; when set to a reviewer-gated pack (e.g. `reviewer_gated_execution_v1`), the graph will block unless `approval_decision` is already set (e.g. via resume) or pre-injected in state.  
   - For runs that use interrupt_for_approval, the approval token is supplied by: (1) **Review UI** — Approve or Reject, then click **Resume run** (calls POST `/v1/reviews/{thread_id}/resume`); or (2) **CLI** — `obr resume <thread_id> --decision approved|rejected`. Resume requires a checkpointer (e.g. `CHECKPOINTER=postgres`, `DATABASE_URL`). See `docs/architecture/review-surface.md`.

## Failure modes

- **Pack not loadable:** If `policy_pack_name` or `OBR_POLICY_PACK` refers to a missing or invalid pack file, the runtime falls back to the default pack (strict) and logs a warning. Reviewer-gated behavior is then determined by that default (typically not reviewer-gated).
- **Missing approval token:** When the pack has `reviewer_gated_execution` and `approval_decision` is unset or `pending`, `policy_review` returns `decision: blocked`, `reasons: [REASON_MISSING_APPROVAL_TOKEN]`. The graph terminates without running patch policy evaluation.
- **Resume without checkpoint:** `obr resume` requires a checkpointer (e.g. `CHECKPOINTER=postgres` or in-process MemorySaver). If the initial run did not use a checkpointer, resume has no prior state and may not behave as expected; ensure the same process or a shared checkpointer is used for run then resume.

**See also:** [policy-model.md](policy-model.md), [review-surface.md](review-surface.md), [runtime-graph.md](runtime-graph.md), [multi-agent-protocol.md](multi-agent-protocol.md).
