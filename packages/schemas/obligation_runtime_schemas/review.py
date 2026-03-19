"""Review payload schema for policy-triggered human approval."""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field, field_validator

from .batch import AxiomAuditResult
from .common import StrictModel
from .policy import PolicyAuditTrail, PolicyDecision
from .witness import AcceptanceSummary


class ReviewObligationSummary(StrictModel):
    """Obligation context shown in the review UI."""

    model_config = ConfigDict(extra="ignore")

    obligation: dict[str, Any] = Field(default_factory=dict)
    target_files: list[str] = Field(default_factory=list)
    target_declarations: list[str] = Field(default_factory=list)

    @field_validator("target_files", "target_declarations", mode="before")
    @classmethod
    def _none_to_list(cls, v: Any) -> list[str]:
        if v is None:
            return []
        return list(v) if isinstance(v, (list, tuple)) else []


class ReviewEnvironmentSummary(StrictModel):
    """Environment fingerprint subset for review display."""

    model_config = ConfigDict(extra="ignore")

    repo_id: str = ""
    repo_url: str | None = None
    commit_sha: str = ""
    lean_toolchain: str = ""
    lakefile_hash: str = ""
    manifest_hash: str | None = None
    target_platform: str = "linux/amd64"
    build_flags: list[str] = Field(default_factory=list)
    os_family: str = "linux"
    imported_packages: list[str] | None = None


class ReviewPatchMetadata(StrictModel):
    """Patch and diff context for reviewers."""

    model_config = ConfigDict(extra="ignore")

    current_patch: dict[str, str] = Field(default_factory=dict)
    protected_paths_touched: bool = False
    imports_changed: bool = False
    changed_files: list[str] = Field(default_factory=list)
    diff_hash: str | None = None

    @field_validator("protected_paths_touched", mode="before")
    @classmethod
    def _protected_paths_touched(cls, v: Any) -> bool:
        """`summarize_patch` emits a list of touched paths; coerce to bool."""
        if isinstance(v, list):
            return len(v) > 0
        return bool(v)

    @field_validator("current_patch", mode="before")
    @classmethod
    def _coerce_patch(cls, v: Any) -> dict[str, str]:
        if v is None:
            return {}
        if not isinstance(v, dict):
            return {}
        return {str(k): str(val) if val is not None else "" for k, val in v.items()}


class ReviewPayload(StrictModel):
    """Payload served to the review UI for interrupted obligations."""

    model_config = ConfigDict(extra="ignore")

    thread_id: str
    obligation_id: str = ""
    obligation_summary: ReviewObligationSummary = Field(default_factory=ReviewObligationSummary)
    environment_summary: ReviewEnvironmentSummary = Field(default_factory=ReviewEnvironmentSummary)
    patch_metadata: ReviewPatchMetadata = Field(default_factory=ReviewPatchMetadata)
    diff_summary: str | None = None
    diagnostics_summary: list[dict[str, Any]] = Field(default_factory=list)
    axiom_audit_summary: AxiomAuditResult = Field(
        default_factory=lambda: AxiomAuditResult(ok=True, trust_level="clean", blocked_reasons=[])
    )
    batch_summary: AcceptanceSummary = Field(default_factory=AcceptanceSummary)
    policy_summary: PolicyDecision = Field(
        default_factory=lambda: PolicyDecision(decision="accepted", trust_level="clean", reasons=[])
    )
    trust_delta: str | None = None
    reasons: list[str] = Field(default_factory=list)
    status: str = "awaiting_review"
    policy_audit: PolicyAuditTrail | None = None

    @field_validator("diagnostics_summary", mode="before")
    @classmethod
    def _coerce_diagnostics(cls, v: Any) -> list[dict[str, Any]]:
        if v is None:
            return []
        if isinstance(v, list):
            return [x for x in v if isinstance(x, dict)]
        if isinstance(v, dict):
            inner = v.get("diagnostics")
            if isinstance(inner, list):
                return [x for x in inner if isinstance(x, dict)]
            return []
        return []

    @field_validator("axiom_audit_summary", mode="before")
    @classmethod
    def _coerce_axiom(cls, v: Any) -> Any:
        if v is None or v == {}:
            return AxiomAuditResult(ok=True, trust_level="clean", blocked_reasons=[])
        return v

    @field_validator("batch_summary", mode="before")
    @classmethod
    def _coerce_batch(cls, v: Any) -> Any:
        if v is None or v == {}:
            return AcceptanceSummary()
        if isinstance(v, dict):
            keep = (
                "ok",
                "trust_level",
                "reasons",
                "build",
                "axiom_audit",
                "fresh_checker",
            )
            return {k: v[k] for k in keep if k in v} or AcceptanceSummary()
        return v

    @field_validator("policy_summary", mode="before")
    @classmethod
    def _coerce_policy(cls, v: Any) -> Any:
        if v is None or v == {}:
            return PolicyDecision(decision="accepted", trust_level="clean", reasons=[])
        return v
