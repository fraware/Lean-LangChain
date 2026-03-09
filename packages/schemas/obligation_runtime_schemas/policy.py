from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import StrictModel


class PolicyDecision(StrictModel):
    decision: Literal["accepted", "rejected", "blocked", "needs_review", "lower_trust", "failed"]
    trust_level: Literal["clean", "warning", "blocked"]
    reasons: list[str] = Field(default_factory=list)
