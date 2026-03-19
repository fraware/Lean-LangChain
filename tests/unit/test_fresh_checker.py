"""Unit tests for FreshChecker and FreshCheckerReal."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from lean_langchain_gateway.batch.fresh_checker import (
    FreshChecker,
    FreshCheckerReal,
)


def test_fresh_checker_test_double_returns_ok() -> None:
    """FreshChecker used as test double (injected in conftest) returns ok=True."""
    checker = FreshChecker()
    result = checker.run(Path("/ws"))
    assert result.ok is True
    assert "lean4checker" in result.command or result.command == ["lean4checker", "--fresh"]
    assert result.timing_ms == 0


def test_fresh_checker_real_returns_ok_when_command_succeeds() -> None:
    """FreshCheckerReal returns ok=True when subprocess returns 0."""
    with patch("lean_langchain_gateway.batch.fresh_checker.subprocess.run") as run:
        run.return_value = type("R", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()
        checker = FreshCheckerReal(timeout_seconds=5.0)
        result = checker.run(Path("/ws"))
    assert result.ok is True
    assert result.stdout == "ok"
    assert result.timing_ms >= 0


def test_fresh_checker_real_returns_not_ok_when_command_fails() -> None:
    """FreshCheckerReal returns ok=False when subprocess returns non-zero."""
    with patch("lean_langchain_gateway.batch.fresh_checker.subprocess.run") as run:
        run.return_value = type("R", (), {"returncode": 1, "stdout": "", "stderr": "not fresh"})()
        checker = FreshCheckerReal(timeout_seconds=5.0)
        result = checker.run(Path("/ws"))
    assert result.ok is False
    assert "not fresh" in result.stderr


def test_fresh_checker_real_handles_os_error() -> None:
    """FreshCheckerReal returns ok=False on OSError (e.g. command not found)."""
    with patch("lean_langchain_gateway.batch.fresh_checker.subprocess.run") as run:
        run.side_effect = OSError("lean4checker not found")
        checker = FreshCheckerReal(timeout_seconds=5.0)
        result = checker.run(Path("/ws"))
    assert result.ok is False
    assert "lean4checker" in result.stderr or "not found" in result.stderr


def test_fresh_checker_real_handles_timeout() -> None:
    """FreshCheckerReal returns ok=False on timeout."""
    import subprocess

    with patch("lean_langchain_gateway.batch.fresh_checker.subprocess.run") as run:
        run.side_effect = subprocess.TimeoutExpired(cmd=["lean4checker", "--fresh"], timeout=5)
        checker = FreshCheckerReal(timeout_seconds=5.0)
        result = checker.run(Path("/ws"))
    assert result.ok is False
    assert "exceeded" in result.stderr.lower()
