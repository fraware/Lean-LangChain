"""HTTP models for orchestrator observability endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import StrictModel


class OrchestratorCapabilityBlock(StrictModel):
    checkpointer: str
    policy_pack_ref: str
    gateway_url_configured: bool
    langgraph_runtime: bool


class OrchestratorHealthResponse(StrictModel):
    status: Literal["ok"]
    version: str
    degraded: bool
    degraded_reasons: list[str] = Field(default_factory=list)
    capabilities: OrchestratorCapabilityBlock


class OrchestratorReadyResponse(StrictModel):
    status: Literal["ready"]
    version: str
    degraded: bool
    degraded_reasons: list[str] = Field(default_factory=list)
    capabilities: OrchestratorCapabilityBlock
