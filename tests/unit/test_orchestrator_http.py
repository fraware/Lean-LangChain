"""Orchestrator HTTP /health and /ready surface."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from obligation_runtime_orchestrator.http_server import create_app


def test_health_returns_capabilities() -> None:
    app = create_app()
    with TestClient(app) as client:
        r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert "version" in data
    assert "degraded" in data
    assert "degraded_reasons" in data
    caps = data.get("capabilities") or {}
    assert "checkpointer" in caps
    assert "policy_pack_ref" in caps


def test_ready_returns_200_or_503() -> None:
    app = create_app()
    with TestClient(app) as client:
        r = client.get("/ready")
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        assert r.json().get("status") == "ready"
