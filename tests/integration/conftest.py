"""Integration-test fixtures: request adapter, SDK client, and graph against TestClient-backed gateway."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from obligation_runtime_sdk import ObligationRuntimeClient, RequestAdapter


@pytest.fixture
def gateway_tc(gateway_app):
    """TestClient for the gateway app; use when a test needs tc without building client/graph."""
    with TestClient(gateway_app) as tc:
        yield tc


def make_testclient_request_adapter(tc: TestClient) -> RequestAdapter:
    """Build a RequestAdapter that forwards POST/GET to a Starlette TestClient. Used for in-process tests."""

    def adapter(method: str, path: str, body: Any) -> dict:
        if method == "POST":
            r = tc.post(path, json=body if body is not None else {})
        else:
            r = tc.get(path)
        r.raise_for_status()
        return r.json()

    return adapter


@pytest.fixture
def sdk_client(gateway_app) -> Any:
    """ObligationRuntimeClient that talks to gateway_app via TestClient. Use in integration tests that need the SDK."""
    with TestClient(gateway_app) as tc:
        adapter = make_testclient_request_adapter(tc)
        client = ObligationRuntimeClient(base_url="http://testserver", request_adapter=adapter)
        yield client


@pytest.fixture
def obr_graph(sdk_client: ObligationRuntimeClient) -> Any:
    """Patch-admissibility graph built with sdk_client. Use in integration tests that invoke the graph."""
    from obligation_runtime_orchestrator.runtime.graph import build_patch_admissibility_graph

    return build_patch_admissibility_graph(client=sdk_client)
