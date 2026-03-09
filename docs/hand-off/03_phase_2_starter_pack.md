# Obligation Runtime — Phase 2 Starter Pack

## Scope

Implement the next engineering layer:

4. Acceptance lane
5. Gateway HTTP API + SDKs
6. LangChain tool layer
7. LangGraph obligation runtime
8. Policy engine and policy packs

By the end of this phase, the team should have:
- a working authoritative acceptance lane (`lake build`, axiom audit, fresh checker)
- a stable Lean Gateway API
- Python and TypeScript SDKs
- a LangChain tool package
- a LangGraph patch-admissibility runtime
- a deterministic policy engine with versioned packs
- terminal states producing `WitnessBundle`

## Prompt 04 — Acceptance lane

Add schemas:
- `BatchBuildResult`
- `AxiomDependency`
- `AxiomAuditResult`
- `FreshCheckerResult`
- `BatchVerifyResult`

Implement:
- `build_runner.py`
- `axiom_audit.py`
- `fresh_checker.py`
- `combine.py`

Hard rule:
- interactive success is necessary but not sufficient
- acceptance requires `lake build`, `#print axioms`, `lean4checker --fresh`

Classification rules:
- `blocked` if `sorryAx`
- `blocked` if unexpected custom axioms under strict policy
- `warning` if `Lean.trustCompiler`
- `clean` otherwise

Tests:
- clean theorem
- theorem using `sorry`
- custom axiom case
- interactive-pass / batch-fail case

## Prompt 05 — Gateway HTTP API and SDKs

Expose endpoints:
- `POST /v1/environments/open`
- `POST /v1/sessions`
- `POST /v1/sessions/{id}/apply-patch`
- `POST /v1/sessions/{id}/interactive-check`
- `POST /v1/sessions/{id}/goal`
- `POST /v1/sessions/{id}/hover`
- `POST /v1/sessions/{id}/definition`
- `POST /v1/sessions/{id}/batch-verify`

Add:
- Python SDK
- TypeScript SDK
- normalized error envelope
- OpenAPI docs

## Prompt 06 — LangChain tool layer

Build thin tools wrapping the Gateway:
- `open_environment_tool`
- `create_session_tool`
- `apply_patch_tool`
- `check_interactive_tool`
- `get_goal_tool`
- `hover_tool`
- `definition_tool`
- `batch_verify_tool`

Design rule:
- tool layer is transport and schema adaptation only
- no policy logic in tools

## Prompt 07 — LangGraph obligation runtime

V1 obligation family:
- `patch_admissibility`

State fields must include:
- thread_id
- obligation_id
- environment_fingerprint
- session_id
- obligation
- target_files
- target_declarations
- current_patch
- patch_history
- interactive_result
- goal_snapshots
- batch_result
- policy_decision
- trust_level
- approval_required
- approval_decision
- status
- attempt_count
- max_attempts
- artifacts
- trace_events

Nodes:
- `init_environment`
- `retrieve_context`
- `draft_candidate`
- `interactive_check`
- `repair_from_diagnostics`
- `repair_from_goals`
- `audit_trust`
- `policy_review`
- `interrupt_for_approval`
- `batch_verify`
- `finalize`

Routing:
- interactive errors => repair or fail
- open goals => repair
- clean interactive => batch verify
- blocked trust => reject or review
- needs review => interrupt
- accepted => finalize

Important simplification:
- do not overbuild autonomous repair yet
- stabilize runtime and evidence plumbing first

## Prompt 08 — Policy engine and policy packs

Build:
- `PolicyPack` model
- pure `PolicyEngine`
- explanation helper
- YAML packs:
  - `strict_patch_gate_v1`
  - `protected_module_review_v1`
  - `engineering_assist_v1`
  - `experimental_low_trust_v1`

V1 policy rules:
- accept only clean batch + trust-clean + no review trigger
- review on protected path changes, import changes, trust deltas
- reject on `sorryAx`, disallowed custom axioms, build failure, checker failure

Stable reason codes:
- `interactive_errors_present`
- `open_goals_remaining`
- `lake_build_failed`
- `fresh_checker_failed`
- `sorry_ax_detected`
- `unexpected_custom_axiom_detected`
- `trust_compiler_detected`
- `protected_path_touched`
- `imports_changed_requires_review`
- `trust_delta_requires_review`
- `human_approved`
- `human_rejected`

## Phase 2 stage gate

Phase 2 is complete only if:
- batch verification works on real fixtures
- trust classification is deterministic
- Gateway API + SDKs are usable end-to-end
- LangChain tools work against live Gateway
- LangGraph runtime executes a full patch-admissibility flow
- interrupt/resume works
- terminal states emit V1 `WitnessBundle`
