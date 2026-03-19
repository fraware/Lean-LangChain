"""Minimal valid gateway JSON dicts for request_adapter stubs (SDK Pydantic validation)."""

from __future__ import annotations

from typing import Any

# InteractiveCheckApiResponse-shaped payload for "sorry" / failed interactive check.
STUB_INTERACTIVE_CHECK_SORRY: dict[str, Any] = {
    "ok": False,
    "phase": "interactive",
    "diagnostics": [
        {
            "severity": "error",
            "file": "Mini/Basic.lean",
            "line": 1,
            "column": 1,
            "message": "sorry",
        }
    ],
    "goals": [],
}
