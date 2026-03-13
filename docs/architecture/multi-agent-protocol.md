# Multi-agent protocol

Protocol events and obligation classes for multi-agent coordination: handoff legality, reviewer gate, lock ownership, and related checks. See [runtime-graph.md](runtime-graph.md) and [policy-model.md](policy-model.md).

## ProtocolEvent

`packages/protocol/obligation_runtime_protocol/models.py` — Event shape: `event_id`, `kind` (claim, delegate, approve, reject, lock, release, execute, recover), `actor` (AgentRef: agent_id, role), `task` (TaskRef: task_id, task_class), optional `payload`, `prior_event_ids`.

Events are supplied as a list of dicts (or models) to the protocol evaluator; they are normalized to dicts with `kind`, `actor`, `task` before evaluation.

## Obligation classes

- **handoff_legality** — When pack has `single_owner_handoff`, delegate must be from the same owner as the prior claim. Otherwise rejected with `REASON_OWNER_MISMATCH` or `REASON_DELEGATE_WITHOUT_PRIOR_CLAIM`.
- **reviewer_gated** — When pack has `reviewer_gated_execution`, events must contain an `approve` event. Otherwise blocked with `REASON_MISSING_APPROVAL_TOKEN`.
- **lock_ownership_invariant** — When pack has `lock_ownership_invariant`, only one holder per resource; release must be by holder; no lock while held by another. Violations yield `REASON_LOCK_CONFLICT` or `REASON_RELEASE_WITHOUT_LOCK`.
- **delegation_admissibility** — When pack has `delegation_admissibility`, delegate only after claim; same or allowed task. Violations yield rejection with appropriate reason.
- **state_transition_preservation** — When pack has `state_transition_preservation`, execute/recover only after an approve event. Otherwise rejected with `REASON_INVALID_STATE_TRANSITION`.
- **artifact_admissibility** — When pack has `artifact_admissibility`, only certain event kinds (e.g. approve, execute) may carry artifacts. Otherwise rejected with `REASON_ARTIFACT_NOT_ADMISSIBLE`.
- **side_effect_authorization** — When pack has `side_effect_authorization`, execute and recover only after approve. Otherwise rejected with `REASON_SIDE_EFFECT_UNAUTHORIZED`.
- **evidence_complete_execution_token** — When pack has `evidence_complete_execution_token`, events or payload must indicate evidence bundle complete (e.g. execute event with `evidence_complete: true`). Otherwise blocked with `REASON_EVIDENCE_INCOMPLETE`.

Reason codes and decisions are in `packages/policy/obligation_runtime_policy/constants.py`.

## Policy packs

Packs that enable protocol checks: `single_owner_handoff_v1`, `reviewer_gated_execution_v1`, `lock_ownership_invariant_v1`, `evidence_complete_execution_token_v1`. Packs such as `strict_patch_gate_v1` include the V2 protocol flags with default false; use `_make_pack_for_obligation_class` or a dedicated pack for delegation_admissibility, state_transition_preservation, etc. Load via `load_pack(name)`; use with `obr run-protocol-obligation --obligation-class <class> --pack <name> --events-file events.json`.

## Runtime integration

State field `protocol_events` (optional) holds events produced during the run. When non-empty, the graph node `evaluate_protocol` runs every pack-enabled protocol check (handoff_legality, lock_ownership_invariant, delegation_admissibility, state_transition_preservation, artifact_admissibility, side_effect_authorization, evidence_complete_execution_token); first rejection/block sets `policy_decision` and terminates without overwriting in `policy_review`. Events can be passed via `obr run-patch-obligation --protocol-events-file events.json` or set in initial state. See `docs/architecture/runtime-graph.md`.

## CLI

- **Offline:** `obr run-protocol-obligation --obligation-class <class> --pack <name> --events-file events.json` where `<class>` is one of: handoff_legality, reviewer_gated, lock_ownership_invariant, delegation_admissibility, state_transition_preservation, artifact_admissibility, side_effect_authorization, evidence_complete_execution_token.
- **In-graph:** `obr run-patch-obligation --policy-pack <pack> --protocol-events-file events.json` (events are merged into state and evaluated in the graph).

Demo scenarios and examples: `docs/demos/README.md` (Handoff legality, Lock ownership invariant, Multi-agent execution without reviewer token).

**See also:** [runtime-graph.md](runtime-graph.md), [policy-model.md](policy-model.md), [reviewer-gated-execution.md](reviewer-gated-execution.md), [demos/README.md](../demos/README.md).
