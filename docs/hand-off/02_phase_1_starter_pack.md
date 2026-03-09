# Obligation Runtime — Phase 1 Starter Pack

## Scope

Implement the first three engineering prompts:

1. Bootstrap the monorepo, ADRs, and core schemas
2. Implement `EnvironmentFingerprint` and workspace snapshotting
3. Build the Lean Gateway interactive lane

By the end of this phase, the team should have:
- a working monorepo scaffold
- versioned Pydantic schemas for the core primitives
- deterministic canonical hashing
- reproducible `EnvironmentFingerprint` generation
- immutable base snapshots + writable overlays
- a first Lean Gateway interactive API with session leasing and normalized outputs
- green integration tests against at least one small Lean fixture repo

## Repo skeleton

```text
obligation-runtime/
  pyproject.toml
  Makefile
  docs/adrs/
  docs/architecture/
  apps/orchestrator/
  apps/lean-gateway/
  packages/schemas/
  packages/sdk-py/
  packages/sdk-ts/
  tests/unit/
  tests/integration/
  scripts/export_json_schemas.py
```

## Engineering constraints

- Python 3.12+
- Pydantic v2
- Ruff, Black, Mypy, Pytest
- no implicit globals for stateful services
- all persisted models must be versioned
- all normalized records must be JSON-stable
- no raw subprocess output returned as API surface
- file/path operations must be safe against traversal

## Prompt 01 — Bootstrap monorepo and schemas

Create:
- root `pyproject.toml`
- `Makefile`
- `README.md`
- `docs/adrs/ADR-0001..0005`
- `packages/schemas/` with:
  - `common.py`
  - `hashing.py`
  - `environment.py`
  - `obligation.py`
  - `diagnostics.py`
  - `interactive.py`
  - `policy.py`
  - `witness.py`
  - `errors.py`
- `scripts/export_json_schemas.py`

Required schema models:
- `EnvironmentFingerprint`
- `ObligationTarget`
- `ObligationPolicy`
- `Obligation`
- `Diagnostic`
- `GoalSnapshot`
- `InteractiveCheckResult`
- `PolicyDecision`
- `WitnessBundle`

Key design rules:
- use `extra="forbid"`
- all top-level records versioned
- canonical JSON hashing stable across runs

Tests:
- schema round-trip
- hash stability
- schema export

## Prompt 02 — Environment fingerprints and snapshots

Build:
- `fingerprint.py`
- `snapshot_store.py`
- `overlay_fs.py`
- `models.py`

Core rules:
- fingerprint = repo + commit + toolchain + lakefile + manifest + platform + build flags
- same fingerprint => same immutable base snapshot
- overlays are per-session and writable
- base snapshots are never mutated by overlays

Directory model:

```text
.var/
  environments/<fingerprint_id>/base/
  environments/<fingerprint_id>/meta.json
  overlays/<session_id>/work/
  overlays/<session_id>/meta.json
```

Tests:
- same repo / same commit => same fingerprint
- snapshot reuse works
- overlay does not mutate base

## Prompt 03 — Interactive Lean Gateway

Build:
- `session_manager.py`
- `worker_pool.py`
- `interactive_api.py`
- `normalizers.py`
- transport boundary for real Lean integration

The public interactive contract should support:
- `open_session`
- `apply_patch`
- `check_interactive`
- `get_goal`
- `hover`
- `definition`

Normalize:
- diagnostics
- goals
- timing
- stdout / stderr

Important:
- session affinity matters
- worker pools are keyed by environment fingerprint
- do not leak raw LSP wire format upward

Tests:
- worker pool reuse
- open session and interactive check
- real Lean fixture integration path or clean transport boundary

## Phase 1 stage gate

Phase 1 is complete only if:
- schemas are stable enough for downstream use
- hashes are deterministic
- snapshots reuse correctly
- overlays are isolated
- interactive lane returns normalized schema objects
- at least one real Lean fixture repo exists

## Deliverables

- scaffolded repo
- core schema package
- environment snapshot substrate
- interactive lane substrate
- ADRs and architecture notes
