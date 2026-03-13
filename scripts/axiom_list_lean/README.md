# Axiom list producer

**Purpose:** Version-controlled producer for per-declaration axiom evidence; used when `OBR_AXIOM_AUDIT_CMD` points here. **Audience:** operators and contributors.

Outputs lines in the gateway contract format so `AxiomAuditorReal` can fill `AxiomAuditResult.dependencies`.

## Contract

- **Invocation:** Gateway runs the producer with `cwd` = workspace path. Exit 0 = ok; non-zero = axiom audit failed.
- **Stdout:** Optional lines in the form `declaration_name: axiom1, axiom2` (one per declaration). Parsed by `_parse_axiom_stdout` in the gateway.

## Usage

For real axiom evidence (not just build success/failure), set:

```bash
OBR_AXIOM_AUDIT_CMD="bash /absolute/path/to/scripts/axiom_list_lean/run_axiom_list.sh"
OBR_USE_REAL_AXIOM_AUDIT=1
```

The script runs `lake build` in the workspace, then `lake exe axiom_list` if the workspace defines that target. Workspaces that want per-declaration output must add a Lake executable target named `axiom_list` that prints one line per declaration in the contract format.

## Example workspace

`tests/integration/fixtures/lean-mini` has an `axiom_list` executable (see `AxiomList.lean` and `lakefile.toml`). When the producer runs there, stdout includes e.g. `Mini.add_zero_right: (none)` and the gateway parses it into `dependencies`.

## Backward compatibility

Default remains `lake build` unless the operator sets `OBR_AXIOM_AUDIT_CMD`. For real axiom evidence, set it to this producer (or to `scripts/axiom_audit_lean.sh`, which also runs `lake exe axiom_list` when present).

**See also:** [docs/architecture/acceptance-lane.md](../../docs/architecture/acceptance-lane.md), [docs/running.md](../../docs/running.md), [../README.md](../README.md).
