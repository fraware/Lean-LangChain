from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import StrictModel, VersionedRecord


class BatchBuildResult(VersionedRecord):
    ok: bool
    command: list[str] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    timing_ms: int = 0


class AxiomDependency(StrictModel):
    declaration: str
    axioms: list[str] = Field(default_factory=list)


class AxiomAuditResult(VersionedRecord):
    ok: bool
    trust_level: Literal["clean", "warning", "blocked"]
    blocked_reasons: list[str] = Field(default_factory=list)
    dependencies: list[AxiomDependency] = Field(default_factory=list)


class FreshCheckerResult(VersionedRecord):
    ok: bool
    command: list[str] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    timing_ms: int = 0


class BatchVerifyResult(VersionedRecord):
    ok: bool
    build: BatchBuildResult
    axiom_audit: AxiomAuditResult
    fresh_checker: FreshCheckerResult
    trust_level: Literal["clean", "warning", "blocked"]
    reasons: list[str] = Field(default_factory=list)
    # Evidence completeness: true when real axiom audit / fresh checker were used.
    axiom_evidence_real: bool = False
    fresh_evidence_real: bool = False
