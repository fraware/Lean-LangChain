# Obligation Runtime — Phase 3 Starter Pack

## Scope

Implement the final execution layer:

9. Review API and review UI
10. Telemetry, LangSmith, and OpenTelemetry integration
11. Evaluation corpus and regression harness
12. Worker isolation and tenancy hardening
13. Persistent MCP adapter
14. V2 multi-agent protocol packs
15. Pilot integration and CLI

By the end of this phase, the team should have:
- a human review surface for policy-triggered approvals
- structured telemetry and LangSmith experiment wiring
- regression corpus with golden cases
- isolated Lean workers
- persistent MCP adapter with session affinity
- V2 typed protocol packs for multi-agent coordination
- pilot CLI and reproducible demo docs

## Prompt 09 — Review API and UI

Add endpoints:
- `GET /v1/reviews/{thread_id}`
- `POST /v1/reviews/{thread_id}/approve`
- `POST /v1/reviews/{thread_id}/reject`

Review payload should include:
- obligation summary
- environment summary
- patch metadata and diff
- diagnostics summary
- axiom audit summary
- batch summary
- policy summary
- trust delta
- reasons

UI panels:
- ObligationSummary
- DiffPanel
- DiagnosticsPanel
- AxiomAuditPanel
- PolicyDecisionPanel
- ApprovalActions

## Prompt 10 — Telemetry and LangSmith

Emit telemetry for every node and decision:
- span name
- timestamp
- obligation ID
- thread ID
- session ID
- environment fingerprint hash
- node name
- policy pack
- timing
- failure class

Stable span names:
- `obr.init_environment`
- `obr.retrieve_context`
- `obr.interactive_check`
- `obr.batch_verify`
- `obr.audit_trust`
- `obr.policy_review`
- `obr.interrupt_for_approval`
- `obr.finalize`
- `obr.gateway.interactive_check`
- `obr.gateway.batch_verify`

Add LangSmith helpers for:
- dataset creation
- experiment execution
- evaluator comparison
- trace-to-dataset promotion

## Prompt 11 — Evaluation corpus

Build patch fixture families:
- `good_patch`
- `sorry_case`
- `trust_compiler_case`
- `protected_path_case`
- `interactive_pass_batch_fail`

Build multi-agent fixture families:
- `handoff_good`
- `handoff_bad_owner`
- `missing_approval_token`
- `lock_conflict`

Golden case format:
- obligation input
- expected decision
- expected trust level
- expected terminal status
- expected reason codes

## Prompt 12 — Worker isolation

Required controls:
- isolated container or microVM per worker
- base snapshot read-only
- overlay writable only for session
- network disabled by default
- CPU / memory / wall-clock limits
- separate worker classes for interactive vs batch
- cleanup and leak detection

## Prompt 13 — Persistent MCP adapter

Hard rule:
- do **not** implement a naive stateless MCP wrapper

Required tools:
- `obligation/open_environment`
- `obligation/create_session`
- `obligation/apply_patch`
- `obligation/check_interactive`
- `obligation/get_goal`
- `obligation/batch_verify`
- `obligation/get_review_payload`
- `obligation/submit_review_decision`

Session affinity must be preserved via:
- thread ID
- gateway session ID
- environment fingerprint

## Prompt 14 — V2 multi-agent protocol packs

Typed protocol events:
- `claim`
- `delegate`
- `approve`
- `reject`
- `lock`
- `release`
- `execute`
- `recover`

V2 obligation classes:
- `delegation_admissibility`
- `handoff_legality`
- `state_transition_preservation`
- `artifact_admissibility`
- `side_effect_authorization`

Policy packs:
- `single_owner_handoff_v1`
- `reviewer_gated_execution_v1`
- `lock_ownership_invariant_v1`
- `evidence_complete_execution_token_v1`

## Prompt 15 — Pilot integration

Add CLI commands:
- `obr open-environment`
- `obr create-session`
- `obr run-patch-obligation`
- `obr run-protocol-obligation`
- `obr review`
- `obr artifacts`
- `obr regressions`

Demo scenarios:
1. clean patch => accepted
2. patch with `sorry` => rejected
3. protected path patch => review required
4. interactive-pass / batch-fail => rejected
5. multi-agent execution without reviewer token => blocked

## Phase 3 stage gate

Phase 3 is complete only if:
- interrupted obligations can be reviewed and resumed from UI
- traces exist for every runtime node
- LangSmith experiments run on a fixed corpus
- isolated workers pass hardening tests
- persistent MCP preserves session affinity
- at least one multi-agent coordination pack works on typed protocol events
- pilot demo scenarios are reproducible from docs only
