# Obligation Runtime — Full Engineering Handoff

This zip is the complete handoff package for building **Obligation Runtime**:

> A LangChain / LangGraph / LangSmith-native formal runtime layer that lets high-stakes agent workflows emit formally checkable obligations, resolve them through Lean in the correct Lake workspace, attach witness bundles and trust audits to the result, and gate handoffs, state transitions, patches, and irreversible side effects through reusable policy packs.

## What is included

1. **Full prompt packs** in `docs/hand-off/`
   - End-to-end prompt pack
   - Phase 1 starter pack
   - Phase 2 starter pack
   - Phase 3 starter pack
   - Master execution index

2. **Bootstrap scaffold** for the repository
   - root workspace files
   - core schemas
   - hashing
   - environment fingerprinting
   - snapshots and overlays
   - interactive Lean Gateway skeleton
   - fixture Lean repo
   - unit/integration test skeletons

3. **Architecture docs + ADRs**

4. **Manifest** of included files

## How engineers should use this

Read and execute in this order:

1. `docs/hand-off/01_end_to_end_cursor_prompt_pack.md`
2. `docs/hand-off/02_phase_1_starter_pack.md`
3. `docs/hand-off/03_phase_2_starter_pack.md`
4. `docs/hand-off/04_phase_3_starter_pack.md`
5. `docs/hand-off/05_master_execution_index.md`

Then begin implementation from the existing scaffold in this repo.

## Hard architectural invariants

- Lean is the only semantic authority.
- Interactive lane is never the final acceptance gate.
- The environment is the unit of reuse, not the proof text.
- Every terminal decision must emit a WitnessBundle.
- Human approval is triggered only by policy deltas.
- All external boundaries use versioned schemas.
- No trace, no trust.

## Suggested first milestone

Get the following green before expanding:

- schemas export cleanly
- `EnvironmentFingerprint` is deterministic
- snapshot reuse works
- overlays are isolated
- interactive lane returns normalized schema objects
- fixture repo tests are green

## Status of this bundle

This is a **starter scaffold + engineering handoff**, not a finished implementation.
It is designed so your Cursor engineers can start immediately with minimal ambiguity.
