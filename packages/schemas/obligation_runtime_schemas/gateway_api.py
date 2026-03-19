"""HTTP request/response models for the Lean Gateway OpenAPI surface."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import ConfigDict, Field

from .common import StrictModel
from .environment import EnvironmentFingerprint
from .interactive import InteractiveCheckResult


class OpenEnvironmentRequest(StrictModel):
    repo_id: str
    repo_path: str | None = None
    repo_url: str | None = None
    commit_sha: str | None = Field(default="HEAD")


class OpenEnvironmentResponse(StrictModel):
    fingerprint: EnvironmentFingerprint
    fingerprint_id: str
    snapshot_path: str


class CreateSessionRequest(StrictModel):
    fingerprint_id: str


class CreateSessionResponse(StrictModel):
    session_id: str
    fingerprint_id: str
    workspace_path: str


class ApplyPatchRequest(StrictModel):
    files: dict[str, str]


class ApplyPatchResponse(StrictModel):
    ok: bool = True
    session_id: str
    changed_files: list[str]


class InteractiveCheckRequest(StrictModel):
    file_path: str


class InteractiveCheckApiResponse(InteractiveCheckResult):
    """Interactive check JSON including LSP capability flag."""

    lsp_required: bool = False


class SessionGoalRequest(StrictModel):
    file_path: str
    line: int
    column: int
    goal_kind: str = "plainGoal"


class SessionGoalResponse(StrictModel):
    ok: bool = True
    goal_kind: str
    goals: Any
    line: int
    column: int
    lsp_required: bool = False


class SessionHoverRequest(StrictModel):
    file_path: str
    line: int
    column: int


class SessionHoverResponse(StrictModel):
    ok: bool = True
    contents: Any
    file_path: str
    line: int
    column: int
    lsp_required: bool = False


class SessionDefinitionRequest(StrictModel):
    file_path: str
    line: int
    column: int


class SessionDefinitionResponse(StrictModel):
    ok: bool = True
    locations: Any
    file_path: str
    line: int
    column: int
    lsp_required: bool = False


class BatchVerifyRequest(StrictModel):
    """Batch-verify body; target_files is ignored (legacy) — use target_declarations."""

    model_config = ConfigDict(extra="ignore")

    target_declarations: list[str] = Field(default_factory=list)


class CreatePendingReviewRequest(StrictModel):
    """Minimum fields to create a pending review; additional keys stored as-is."""

    model_config = ConfigDict(extra="allow")

    thread_id: str


class CreatePendingReviewResponse(StrictModel):
    ok: bool = True
    thread_id: str


class ReviewDecisionResponse(StrictModel):
    ok: bool = True
    thread_id: str
    decision: Literal["approved", "rejected"]


class ReviewResumeProxyResponse(StrictModel):
    """Shape returned by orchestrator resume; gateway proxies this."""

    ok: bool = True
    thread_id: str
    status: Any = None
    artifacts_count: int = 0


class GatewayCapabilityBlock(StrictModel):
    lean_interactive: str
    axiom_audit: str
    fresh_checker: str
    review_store: str


class GatewayHealthResponse(StrictModel):
    status: Literal["ok"]
    version: str
    degraded: bool
    capabilities: GatewayCapabilityBlock


class GatewayReadyOkResponse(StrictModel):
    status: Literal["ready"]
    version: str
    degraded: bool
    degraded_reasons: list[str] = Field(default_factory=list)
    capabilities: GatewayCapabilityBlock
