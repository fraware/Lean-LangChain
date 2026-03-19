"""Contract: critical OpenAPI component schemas expose stable, typed field sets for SDK and UI."""

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


def _props(spec: dict, schema_name: str) -> dict:
    schemas = spec.get("components", {}).get("schemas", {})
    assert schema_name in schemas, f"missing schema {schema_name}"
    return schemas[schema_name].get("properties") or {}


def test_review_payload_has_typed_nested_summaries(openapi_spec: dict) -> None:
    p = _props(openapi_spec, "ReviewPayload")
    for key in (
        "thread_id",
        "obligation_summary",
        "environment_summary",
        "patch_metadata",
        "diagnostics_summary",
        "axiom_audit_summary",
        "batch_summary",
        "policy_summary",
        "policy_audit",
    ):
        assert key in p, f"ReviewPayload missing {key!r}"


def test_acceptance_summary_schema_exists(openapi_spec: dict) -> None:
    """Batch/witness acceptance lane shape is documented for clients."""
    schemas = openapi_spec.get("components", {}).get("schemas", {})
    assert "AcceptanceSummary" in schemas
    ap = schemas["AcceptanceSummary"].get("properties") or {}
    assert "ok" in ap and "trust_level" in ap


def test_gateway_health_response_stable_keys(openapi_spec: dict) -> None:
    p = _props(openapi_spec, "GatewayHealthResponse")
    for key in ("status", "version", "degraded", "capabilities"):
        assert key in p, f"GatewayHealthResponse missing {key!r}"


def test_batch_verify_result_has_acceptance_lane_fields(openapi_spec: dict) -> None:
    p = _props(openapi_spec, "BatchVerifyResult")
    for key in ("ok", "trust_level", "build", "axiom_audit", "fresh_checker"):
        assert key in p, f"BatchVerifyResult missing {key!r}"
