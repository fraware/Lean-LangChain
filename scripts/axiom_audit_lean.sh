#!/usr/bin/env bash
# Axiom audit script contract: run from workspace (gateway sets cwd to workspace_path).
# Exit 0 = ok; non-zero = axiom audit failed. Stdout: optional lines "declaration: axiom1, axiom2"
# (one per declaration); AxiomAuditorReal parses these into AxiomAuditResult.dependencies.
# Runs "lake build" then, if the workspace has a Lake executable "axiom_list", runs it to
# print declaration lines. Example: tests/integration/fixtures/lean-mini has axiom_list (lake exe axiom_list).
set -euo pipefail
lake build
if lake exe axiom_list 2>/dev/null; then true; fi
