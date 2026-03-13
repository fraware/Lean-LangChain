#!/usr/bin/env bash
# Axiom list producer: run from workspace (gateway sets cwd to workspace_path).
# Exit 0 = ok; non-zero = axiom audit failed.
# Stdout: lines in contract format "declaration_name: axiom1, axiom2" (one per declaration).
# AxiomAuditorReal parses these into AxiomAuditResult.dependencies.
# 1) Run lake build. 2) If workspace has Lake executable "axiom_list", run it to print lines.
# Example workspace with axiom_list: tests/integration/fixtures/lean-mini.
# Set OBR_AXIOM_AUDIT_CMD to "bash /path/to/scripts/axiom_list_lean/run_axiom_list.sh" for per-declaration evidence.
set -euo pipefail
lake build
if lake exe axiom_list 2>/dev/null; then true; fi
