"""Shared pytest fixtures for Obligation Runtime tests."""

# Inject test doubles before any gateway code uses deps (production path requires real transport/axiom/fresh).
from obligation_runtime_lean_gateway.api import deps as gateway_deps
from obligation_runtime_lean_gateway.server.transport import TestDoubleTransport
from obligation_runtime_lean_gateway.batch.axiom_audit import AxiomAuditor
from obligation_runtime_lean_gateway.batch.fresh_checker import FreshChecker

gateway_deps.set_test_transport(TestDoubleTransport())
gateway_deps.set_test_axiom_auditor(AxiomAuditor())
gateway_deps.set_test_fresh_checker(FreshChecker())

import pytest
from fastapi.testclient import TestClient

from obligation_runtime_lean_gateway.api.app import create_app


@pytest.fixture
def gateway_app():
    """Fresh FastAPI app for the Lean Gateway (function-scoped)."""
    return create_app()


@pytest.fixture
def gateway_client(gateway_app):
    """TestClient bound to the gateway app; use for HTTP requests in tests."""
    with TestClient(gateway_app) as client:
        yield client
