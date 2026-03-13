# Scripts layout

**Purpose:** Index of scripts by purpose (setup, demos, root, axiom producer, fixtures). **Audience:** contributors and operators. All paths are from the repository root.

## Setup

- **setup/install_lean4checker.py** — Clone and build lean4checker (leanprover/lean4checker). Run with `make install-lean4checker` or `python scripts/setup/install_lean4checker.py`. See `docs/running.md` for `OBR_FRESH_CHECK_CMD`.

## Demos

- **demos/run_demo_scenario_1.py** … **run_demo_scenario_5.py** — Reproducible demo scenarios (clean patch, sorry, protected path, batch-fail, reviewer_gated). Run with `make demo-scenario-1` through `make demo-scenario-5`.
- **demos/run_hero_demo.py** — Main demo (hero): scenarios 1, 2, 3 in order. `make demo-hero` or `make demo-hero-ui`. See `docs/demos/main-demo.md`.

## Root scripts

- **export_json_schemas.py** — Export JSON schemas from the schema package. Run via `make export-schemas`.
- **run_benchmark.py** — Pipeline and workload benchmark; see `docs/benchmark.md`. Run with `make benchmark` or `make benchmark-report`.

## Axiom producer

- **axiom_list_lean/run_axiom_list.sh** — Bash script that runs `lake build` and `lake exe axiom_list` in the current directory (workspace). Set `OBR_AXIOM_AUDIT_CMD` to this script for per-declaration axiom evidence. See `scripts/axiom_list_lean/README.md` and `docs/architecture/acceptance-lane.md`.

## Fixtures

- **fixtures/sorry_patch.lean** — Lean snippet used by demo scenario 2 (patch with `sorry`).

**See also:** [docs/demos/README.md](../docs/demos/README.md), [docs/running.md](../docs/running.md), [docs/tests-and-ci.md](../docs/tests-and-ci.md), [docs/architecture/acceptance-lane.md](../docs/architecture/acceptance-lane.md).
