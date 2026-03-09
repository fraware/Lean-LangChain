# Obligation Runtime — End-to-End Cursor Prompt Pack

## Purpose

This document is the engineer handoff for building **Obligation Runtime**: a LangChain/LangGraph/LangSmith-native formal runtime layer that lets high-stakes agent workflows emit formal obligations, resolve them through Lean in the correct Lake workspace, attach witness bundles and trust audits to the result, and gate handoffs, state transitions, patches, and irreversible side effects through reusable policy packs.

This is **not** a theorem-proving toy, a Lean IDE replacement, or a general agent framework. It is a **semantic control plane** for high-trust workflows.

The implementation principle is strict:

- **Lean is the formal semantic authority**.
- **LangGraph is the obligation runtime**.
- **LangChain tools are the execution boundary**.
- **LangSmith is the trace/eval plane**.
- **Policy decides admissibility**.

## Core primitives

### Obligation
A formally checkable claim attached to a workflow step.

Examples:
- `patch_preserves_invariant`
- `handoff_is_authorized`
- `artifact_is_admissible`
- `protected_module_change_requires_review`
- `no_disallowed_axioms_introduced`

### EnvironmentFingerprint
The exact Lean/Lake environment used to decide the obligation.

Fields:
- repo_url
- repo_id
- commit_sha
- lean_toolchain
- lakefile_hash
- manifest_hash
- target_platform
- build_flags
- imported_packages summary

### WitnessBundle
The evidence produced during decision-making.

Fields:
- obligation metadata
- environment fingerprint
- patch diff / artifact hash
- interactive diagnostics
- goal snapshots
- hover/definition context when relevant
- `#print axioms` results
- `lake build` result
- `lean4checker --fresh` result
- policy inputs
- policy decision
- approval payload and human decision if any
- timings
- provenance hashes

### PolicyDecision
One of:
- accepted
- rejected
- blocked
- needs_review
- lower_trust
- failed

## Product boundary

### In scope for V1
- One repo / one environment snapshot at a time
- One target file or declaration set at a time
- Interactive Lean checks via server lane
- Acceptance checks via batch lane
- Obligation runtime for patch admissibility and trust cleanliness
- Review UI for human approval on trust-boundary changes
- LangSmith trace/evaluation integration

### In scope for V2
- Multi-agent handoff legality
- Shared-state transition invariants
- Artifact admissibility for downstream agents
- Reusable policy pack library
- Persistent MCP adapter

### Out of scope
- Open-ended conversational quality verification
- Global plan optimality proofs
- Full theorem-prover benchmark chasing
- Cross-repo autonomous rewrites
- Auto-merge / auto-deploy without policy layer
- Replacing Lean editor UX

## Hard architectural invariants

1. **Interactive lane is never the final acceptance gate.**
2. **Every acceptance decision is tied to an immutable EnvironmentFingerprint.**
3. **All Lean execution is isolated behind Lean Gateway.**
4. **Every obligation emits a WitnessBundle.**
5. **Human review is triggered by policy deltas, not by ordinary repair iterations.**
6. **No raw subprocess output is the system API; everything is normalized.**
7. **All traces are structured and exportable into evaluation datasets.**

## Target monorepo layout

```text
obligation-runtime/
  apps/
    orchestrator/
    lean-gateway/
    review-ui/
  packages/
    schemas/
    graph/
    policy/
    telemetry/
    tools/
    evals/
    fixtures/
    sdk-py/
    sdk-ts/
  infra/
  tests/
  docs/
```

## Recommended stack

- Python for orchestrator, gateway, policy engine, evals
- TypeScript/Next.js for review UI
- FastAPI for HTTP APIs
- Pydantic v2 for schemas
- LangGraph for obligation runtime
- LangChain for tool abstractions
- LangSmith / OpenTelemetry for traces and experiments
- Postgres for persistence
- Redis for queues / coordination if needed
- Docker or microVM isolation for Lean execution

## Canonical data model

### Obligation
```json
{
  "obligation_id": "obl_01...",
  "kind": "patch_admissibility",
  "status": "pending",
  "target": {
    "repo_id": "repo_mathlib_like",
    "file": "Foo/Bar.lean",
    "declarations": ["foo_theorem"]
  },
  "claim": "Patch preserves admissibility under strict theorem policy",
  "inputs": {
    "patch_id": "patch_01...",
    "policy_pack": "strict_patch_gate_v1"
  },
  "environment_fingerprint": {
    "repo_url": "...",
    "commit_sha": "...",
    "lean_toolchain": "leanprover/lean4:4.28.0",
    "lakefile_hash": "...",
    "manifest_hash": "..."
  },
  "policy": {
    "must_pass_axiom_audit": true,
    "allow_trust_compiler": false,
    "require_human_if_imports_change": true
  }
}
```

### WitnessBundle
```json
{
  "bundle_id": "wit_01...",
  "obligation_id": "obl_01...",
  "environment_fingerprint": {},
  "patch": {"patch_id": "patch_01...", "diff": "..."},
  "interactive": {"ok": true, "diagnostics": [], "goals": []},
  "acceptance": {
    "lake_build": {"ok": true},
    "axiom_audit": {"clean": true},
    "fresh_checker": {"ok": true}
  },
  "policy": {
    "decision": "accepted",
    "trust_level": "clean",
    "reasons": ["no_disallowed_axioms"]
  },
  "approval": {"required": false, "decision": null},
  "trace": {"thread_id": "thr_01...", "event_hashes": []}
}
```

## Core workstreams

1. **Schemas and hashing**
2. **Environment fingerprinting and snapshots**
3. **Interactive Lean Gateway**
4. **Acceptance lane**
5. **Gateway API + SDKs**
6. **LangChain tools**
7. **LangGraph runtime**
8. **Policy engine + packs**
9. **Review API/UI**
10. **Telemetry + LangSmith**
11. **Regression corpus**
12. **Worker isolation**
13. **Persistent MCP**
14. **V2 multi-agent protocol packs**
15. **Pilot CLI + docs**

## Coding standards

- Python 3.12+
- full typing, mypy clean
- Ruff + Black + pytest
- structured logging only
- explicit retry/backoff wrappers around external process calls
- stable error taxonomy
- no unbounded recursion in repair loops
- all persisted records versioned
- all user-facing APIs schema-validated

## Stable error taxonomy

- `ParseError`
- `ElaborationError`
- `TypeMismatch`
- `UnknownIdentifier`
- `UnsolvedGoals`
- `ServerProtocolError`
- `WorkspaceConfigError`
- `BuildFailure`
- `AxiomPolicyViolation`
- `CheckerFailure`
- `Timeout`
- `ResourceLimit`
- `HumanRejected`
- `InternalBug`

## Required CI stages

1. lint
2. typecheck
3. schema tests
4. gateway integration tests
5. graph routing tests
6. regression tests
7. trace/eval smoke tests
8. container isolation smoke tests

## Final instruction for engineers

Do not optimize for a demo that “looks agentic.” Optimize for:
- correct environment reproduction
- stable normalized outputs
- deterministic policy evaluation
- replayable witness bundles
- clear acceptance boundaries
- production-grade observability

The product wins when a high-stakes workflow can answer, with evidence:

**what was proposed, in which environment, under which policy, with which proof/audit result, and why the system allowed or blocked it.**
