# Obligation Runtime — Master Execution Index

## Canonical document order

Read and execute in this exact order:

1. End-to-End Cursor Prompt Pack
2. Phase 1 Starter Pack
3. Phase 2 Starter Pack
4. Phase 3 Starter Pack
5. Master Execution Index

## Project-wide invariants

1. Lean is the only semantic authority.
2. Interactive lane is never the final acceptance gate.
3. The environment is the unit of reuse, not the proof text.
4. Every terminal runtime decision must emit a `WitnessBundle`.
5. Human approval is triggered only by policy deltas.
6. No external service boundary may use ad hoc payloads.
7. No trace, no trust.

## Recommended team topology

### Track A — Core semantics and Lean execution
Owns:
- schemas
- hashing
- environment fingerprinting
- snapshots/overlays
- interactive lane
- acceptance lane
- worker isolation

### Track B — Runtime and policy
Owns:
- LangGraph runtime
- policy engine
- policy packs
- witness assembly
- interrupt/resume
- CLI

### Track C — API, SDK, and interop
Owns:
- Gateway HTTP API
- Python SDK
- TypeScript SDK
- LangChain tools
- MCP adapter

### Track D — Review, telemetry, and evaluation
Owns:
- review API/UI
- telemetry
- LangSmith integration
- regression corpus
- experiment harness
- operator docs

## Phase-by-phase execution order

### Phase 1 — Foundations
Workstreams:
- monorepo bootstrap
- core schemas
- environment packaging
- interactive lane scaffold

Stage gate:
- schemas are stable
- hashes deterministic
- snapshots reuse correctly
- overlays isolated
- interactive lane normalized

### Phase 2 — Core runtime
Workstreams:
- acceptance lane
- Gateway API + SDKs
- LangChain tools
- LangGraph runtime
- policy engine

Recommended parallelization:
- Track A: acceptance lane
- Track C: API/SDKs + tools
- Track B: policy engine, then runtime

Stage gate:
- batch verification runs on fixtures
- API/SDKs usable end-to-end
- runtime executes full patch-admissibility flow
- interrupt/resume works
- terminal states emit `WitnessBundle`

### Phase 3 — Operability and platformization
Workstreams:
- review surface
- telemetry and LangSmith
- regression corpus
- worker hardening
- MCP adapter
- V2 multi-agent protocol packs
- pilot integration

Stage gate:
- review and resume work
- traces emitted for all nodes
- regressions and experiments run
- worker hardening green
- MCP preserves session affinity
- at least one multi-agent pack works
- pilot demos reproducible from docs

## Dependency graph

```text
Schemas/Hashing
  -> EnvironmentFingerprint/Snapshots
  -> Interactive Lane
  -> Acceptance Lane
  -> API/SDKs
  -> Policy Engine
  -> Runtime
  -> Review/UI
  -> Evals/Telemetry
  -> MCP
  -> Multi-agent V2
```

## Handoff checkpoints

- **Checkpoint A** — schema freeze
- **Checkpoint B** — environment substrate ready
- **Checkpoint C** — Gateway alpha ready
- **Checkpoint D** — policy freeze for V1
- **Checkpoint E** — runtime alpha ready
- **Checkpoint F** — platform beta ready

## Release sequence

- **0.1** Foundation alpha
- **0.2** Runtime alpha
- **0.3** Runtime beta
- **0.4** Pilot candidate
- **0.5** Coordination beta

## First pilot scope

Start with:

### code/change-management patch admissibility

Flow:
- propose patch
- run obligation
- inspect evidence
- review if needed
- accept or reject

Only after that, expand to:
- reviewer-gated execution tokens
- handoff legality
- shared-state lock invariants

## Anti-patterns to avoid

- building review UI before runtime/policy are stable
- making MCP primary before session affinity is solved
- casual reason-code churn
- returning raw Lean/LSP output from APIs
- overbuilding autonomous repair too early
- skipping golden-case regression testing
- adding multi-agent V2 before V1 patch pilot is genuinely usable
