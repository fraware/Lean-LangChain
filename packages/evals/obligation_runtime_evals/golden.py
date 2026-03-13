"""Golden case format for regression: obligation input + expected outcome."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GoldenCase(BaseModel):
    """Single golden case: obligation input and expected decision/trust/status/reasons."""

    case_id: str
    obligation_input: dict[str, Any] = Field(default_factory=dict)
    expected_decision: str = ""
    expected_trust_level: str = ""
    expected_terminal_status: str = ""
    expected_reason_codes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def load_golden_cases(families: list[str]) -> list[GoldenCase]:
    """Load golden cases for given fixture family names. Returns list of GoldenCase."""
    from . import fixtures as fixtures_mod

    out: list[GoldenCase] = []
    for name in families:
        cases = getattr(fixtures_mod, f"FAMILY_{name}", None)
        if cases is None:
            continue
        for c in cases:
            if isinstance(c, dict):
                out.append(GoldenCase.model_validate(c))
            else:
                out.append(c)
    return out
