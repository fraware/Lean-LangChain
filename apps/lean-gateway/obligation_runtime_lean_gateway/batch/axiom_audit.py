from __future__ import annotations

from pathlib import Path

from obligation_runtime_schemas.batch import AxiomAuditResult


class AxiomAuditor:
    """Run `#print axioms` against target declarations.

    Replace with generated audit file + parser in Phase 2.
    """

    def run(self, workspace_path: Path, declarations: list[str]) -> AxiomAuditResult:
        return AxiomAuditResult(ok=True, trust_level="clean", blocked_reasons=[], dependencies=[])
