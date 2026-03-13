# Policy model

The deterministic policy engine, versioned policy packs, patch metadata, and protocol evaluator. See [runtime-graph.md](runtime-graph.md) and [gateway-api.md](gateway-api.md) for context.

## PolicyEngine

`packages/policy/obligation_runtime_policy/engine.py` — Pure, deterministic evaluation over normalized evidence. Inputs: obligation, interactive_result, batch_result, patch_metadata, policy_pack. Output: `PolicyDecision` with `decision`, `trust_level`, `reasons`.

Behavior: rejects on interactive errors or batch failure; blocks on axiom audit blocked_reasons; returns needs_review when trust_compiler detected (and pack disallows), protected_paths_touched, or imports_changed (and pack requires human); otherwise accepted.

## PolicyPack

`packages/policy/obligation_runtime_policy/models.py` — Versioned pack loaded from YAML. Fields include: allow_trust_compiler, block_sorry_ax, require_human_if_imports_change, protected_paths; and V2 protocol flags: single_owner_handoff, reviewer_gated_execution, lock_ownership_invariant, evidence_complete_execution_token, delegation_admissibility, state_transition_preservation, artifact_admissibility, side_effect_authorization.

Packs live under `packages/policy/obligation_runtime_policy/packs/` (e.g. `strict_patch_gate_v1.yaml`, `reviewer_gated_execution_v1.yaml`, `single_owner_handoff_v1.yaml`, `lock_ownership_invariant_v1.yaml`, `evidence_complete_execution_token_v1.yaml`). Load by name via `pack_loader.load_pack(name)`; `list_packs()` returns available pack names.

## Patch metadata

`packages/policy/obligation_runtime_policy/patch_metadata.py` — `summarize_patch(before, after, protected_paths)` returns `changed_files`, `imports_changed`, `protected_paths_touched` (list), `diff_hash`. The graph computes patch_metadata from `current_patch` and `obligation.policy.protected_paths` and passes it to the policy engine and to the review payload in `interrupt_for_approval`. This enables "protected path touched" and "imports changed" to drive needs_review.

## Constants

`packages/policy/obligation_runtime_policy/constants.py` — Canonical reason codes and decision/trust/approval values. Use these everywhere (evaluators, graph, tests, CLI) for consistency:

- Reason codes: `REASON_DELEGATE_WITHOUT_PRIOR_CLAIM`, `REASON_OWNER_MISMATCH`, `REASON_MISSING_APPROVAL_TOKEN`, `REASON_LOCK_CONFLICT`, `REASON_RELEASE_WITHOUT_LOCK`, `REASON_INVALID_STATE_TRANSITION`, `REASON_ARTIFACT_NOT_ADMISSIBLE`, `REASON_SIDE_EFFECT_UNAUTHORIZED`, `REASON_EVIDENCE_INCOMPLETE`
- Decisions: `DECISION_ACCEPTED`, `DECISION_REJECTED`, `DECISION_BLOCKED`, `DECISION_NEEDS_REVIEW`
- Trust: `TRUST_CLEAN`, `TRUST_WARNING`, `TRUST_BLOCKED`
- Approval: `APPROVAL_APPROVED`, `APPROVAL_REJECTED`, `APPROVAL_PENDING`

## Protocol evaluator

`packages/policy/obligation_runtime_policy/protocol_evaluator.py` — Evaluates V2 protocol obligation classes over a list of events (claim, delegate, approve, lock, release, execute, recover, etc.). Events are normalized to dicts with `kind`, `actor`, `task`. Obligation classes: `handoff_legality` (single-owner claim/delegate), `reviewer_gated` (approve token required), `lock_ownership_invariant` (single holder, release by holder), `delegation_admissibility` (delegate only after claim; same or allowed task), `state_transition_preservation` (execute/recover only after approve), `artifact_admissibility` (only certain event kinds may attach artifacts), `side_effect_authorization` (execute/recover only after approve), `evidence_complete_execution_token` (events or payload must indicate evidence bundle complete). Dispatched via `evaluate_protocol_obligation(obligation_class, events, pack)`; returns `PolicyDecision`.

## Runtime integration

The patch-admissibility graph loads the pack by name from state `policy_pack_name` or env `OBR_POLICY_PACK`. The `policy_review` node computes patch_metadata from `summarize_patch(current_patch, obligation.policy.protected_paths)` and passes it to the policy engine; it also applies reviewer_gated check (approval token) when the pack has `reviewer_gated_execution`. The `evaluate_protocol` node runs all pack-enabled protocol checks (handoff_legality, lock_ownership_invariant, delegation_admissibility, state_transition_preservation, artifact_admissibility, side_effect_authorization, evidence_complete_execution_token); first rejection/block wins. The review payload in `interrupt_for_approval` includes patch_metadata (protected_paths_touched, imports_changed, changed_files, diff_hash). See `docs/architecture/runtime-graph.md` and `docs/architecture/reviewer-gated-execution.md`.

**See also:** [runtime-graph.md](runtime-graph.md), [reviewer-gated-execution.md](reviewer-gated-execution.md), [multi-agent-protocol.md](multi-agent-protocol.md), [review-surface.md](review-surface.md).
