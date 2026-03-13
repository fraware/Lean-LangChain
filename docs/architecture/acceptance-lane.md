# Acceptance lane

Batch verification path: build, axiom audit, fresh checker. This is the only final acceptance gate; the interactive check never decides acceptance. See [runtime-graph.md](runtime-graph.md) and [gateway-api.md](gateway-api.md).

The Gateway exposes this via the batch-verify endpoint; the runtime uses the result in the policy engine.

## Components

- **Build:** `lake build` in the session workspace (or container). Success/failure and timing are returned. Timeout via `OBR_BUILD_TIMEOUT`.
- **Axiom audit:** A command runs in the workspace (default: `lake build`; override with `OBR_AXIOM_AUDIT_CMD`). Exit code maps to axiom audit result. For per-declaration axiom evidence, set `OBR_AXIOM_AUDIT_CMD` to a script that prints lines in the contract format `declaration_name: axiom1, axiom2` (one per declaration). The Gateway parses stdout via `_parse_axiom_stdout` into `AxiomAuditResult.dependencies`. In-repo producer: `scripts/axiom_list_lean/run_axiom_list.sh` (runs `lake build` then `lake exe axiom_list` when the workspace defines that target). Example workspace with `axiom_list`: `tests/integration/fixtures/lean-mini` (see `AxiomList.lean` and `lakefile.toml`). See [running.md](../running.md) and `scripts/axiom_list_lean/README.md`.
- **Fresh checker:** When `OBR_USE_REAL_FRESH_CHECKER` is set, runs `lean4checker --fresh` (or `OBR_FRESH_CHECK_CMD`) in the workspace. Requires the binary in PATH. The **fresh** CI job installs Lean 4 and lean4checker (from leanprover/lean4checker) and runs the integration test so the requirement is validated in CI; for local or custom images, provide the binary in PATH.

## Hard rule (OBR_ACCEPTANCE_STRICT)

When `OBR_ACCEPTANCE_STRICT` is set (e.g. `1`), the Gateway enforces the acceptance hard rule: batch-verify returns `ok: false` and `trust_level: blocked` unless both real axiom audit and real fresh checker were used (`axiom_evidence_real` and `fresh_evidence_real` true). This ensures acceptance always requires lake build, #print axioms, and lean4checker --fresh when strict mode is on. Logic lives in `apply_acceptance_strict()` in `batch/combine.py`; the batch-verify route applies it when the env var is set. See [running.md](../running.md) for the variable.

## WitnessBundle evidence

The batch-verify result includes `axiom_evidence_real` and `fresh_evidence_real` (booleans). When both are true, the bundle has full acceptance evidence. Production requires real axiom audit and (when `OBR_ACCEPTANCE_STRICT`) real fresh checker; the gateway raises at use if not configured. Tests inject test doubles via conftest. Set `OBR_USE_REAL_AXIOM_AUDIT` and `OBR_USE_REAL_FRESH_CHECKER` and provide the producer command and `lean4checker` (or override) in PATH to get both flags true.

## Batch-verify result shape

The batch-verify endpoint returns a structured result with: `ok`, `trust_level` (clean / warning / blocked), `build` (command, timing_ms, ok), `axiom_audit` (trust_level, blocked_reasons, optional `dependencies` when the audit command prints declaration lines), `fresh_checker` (ok, command), `reasons` (list of reason codes), and evidence-completeness flags `axiom_evidence_real` and `fresh_evidence_real` (boolean; true when the real axiom auditor and real fresh checker were used).

## Test coverage

- **Unit:** Axiom stdout parsing in `tests/unit/test_axiom_audit.py` (including producer format). Strict hard rule: `tests/unit/test_batch_combine.py` — `test_apply_acceptance_strict_blocks_when_evidence_not_real`, `test_apply_acceptance_strict_no_change_when_both_real`.
- **Integration:** `tests/integration/test_acceptance_lane.py`: structured result shape; real lake build when `lake` in PATH; real axiom audit when `OBR_USE_REAL_AXIOM_AUDIT` set; `test_acceptance_lane_axiom_producer_dependencies_non_empty` when `OBR_AXIOM_AUDIT_CMD` points at the producer and workspace has `axiom_list`; real fresh checker when `OBR_USE_REAL_FRESH_CHECKER` and `lean4checker` in PATH; container runner when `OBR_WORKER_RUNNER=container` and image set; strict mode when `OBR_ACCEPTANCE_STRICT=1` (`test_acceptance_lane_strict_blocks_without_real_evidence`).

**See also:** [runtime-graph.md](runtime-graph.md), [gateway-api.md](gateway-api.md), [interactive-lane.md](interactive-lane.md), [running.md](../running.md).
