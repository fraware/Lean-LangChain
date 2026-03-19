"""Unit tests for Gateway production features: redact_secrets, production state assertion, transport requirement."""

from __future__ import annotations

import os
import subprocess
import sys
from unittest.mock import patch

import pytest

from lean_langchain_gateway.api.errors import redact_secrets


def test_redact_secrets_redacts_database_url() -> None:
    text = "Connection failed: DATABASE_URL=postgresql://user:secret@host/db"
    out = redact_secrets(text)
    assert "postgresql://" not in out
    assert "DATABASE_URL=***" in out or "***" in out


def test_redact_secrets_redacts_password() -> None:
    text = "password=supersecret"
    assert redact_secrets(text) == "password=***"


def test_redact_secrets_leaves_safe_text() -> None:
    text = "Hello world"
    assert redact_secrets(text) == text


def test_production_state_assertion_raises_when_memory_and_obr_env_production() -> None:
    from fastapi.testclient import TestClient

    from lean_langchain_gateway.api.app import create_app

    with patch.dict(
        os.environ,
        {"OBR_ENV": "production", "REVIEW_STORE": "memory", "CHECKPOINTER": "memory"},
        clear=False,
    ):
        with pytest.raises(RuntimeError, match="REVIEW_STORE must not be memory"):
            with TestClient(create_app()):
                pass


def test_lean_transport_required_in_production() -> None:
    """Accessing deps.interactive_api without real transport and without test injection raises RuntimeError."""
    env = os.environ.copy()
    env.pop("OBR_USE_LEAN_LSP", None)
    env.pop("OBR_USE_REAL_LEAN", None)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from lean_langchain_gateway.api import deps; _ = deps.interactive_api",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert (
        "OBR_USE_REAL_LEAN" in result.stderr
        or "OBR_USE_LEAN_LSP" in result.stderr
        or "RuntimeError" in result.stderr
    )
