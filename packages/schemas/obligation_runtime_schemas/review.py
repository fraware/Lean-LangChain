"""Review payload schema for policy-triggered human approval."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import StrictModel


class ReviewPayload(StrictModel):
    """Payload served to the review UI for interrupted obligations."""

    thread_id: str
    obligation_id: str = ""
    obligation_summary: dict[str, Any] = Field(default_factory=dict)
    environment_summary: dict[str, Any] = Field(default_factory=dict)
    patch_metadata: dict[str, Any] = Field(default_factory=dict)
    diff_summary: str | None = None
    diagnostics_summary: dict[str, Any] = Field(default_factory=dict)
    axiom_audit_summary: dict[str, Any] = Field(default_factory=dict)
    batch_summary: dict[str, Any] = Field(default_factory=dict)
    policy_summary: dict[str, Any] = Field(default_factory=dict)
    trust_delta: str | None = None
    reasons: list[str] = Field(default_factory=list)
    status: str = "awaiting_review"
