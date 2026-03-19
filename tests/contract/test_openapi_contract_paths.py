"""Contract: OpenAPI snapshot contains critical gateway paths and components."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
OPENAPI = _REPO / "contracts" / "openapi" / "lean-gateway.json"


@pytest.fixture
def openapi_spec() -> dict:
    assert OPENAPI.is_file(), f"Missing {OPENAPI}; run make export-openapi"
    return json.loads(OPENAPI.read_text(encoding="utf-8"))


def test_openapi_has_session_and_review_paths(openapi_spec: dict) -> None:
    paths = openapi_spec.get("paths", {})
    for p in (
        "/v1/environments/open",
        "/v1/sessions",
        "/v1/sessions/{session_id}/batch-verify",
        "/v1/reviews",
        "/v1/reviews/{thread_id}",
        "/health",
    ):
        assert p in paths, f"missing path {p}"


def test_openapi_defines_batch_and_review_schemas(openapi_spec: dict) -> None:
    schemas = openapi_spec.get("components", {}).get("schemas", {})
    for name in ("BatchVerifyResult", "ReviewPayload", "OpenEnvironmentResponse"):
        assert name in schemas, f"missing schema {name}"
