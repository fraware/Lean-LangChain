"""Unit tests for BuildRunner (delegates to LeanRunner)."""

from __future__ import annotations

from pathlib import Path

from lean_langchain_gateway.batch.build_runner import BuildRunner


class _MockRunner:
    def __init__(self, stdout: str, stderr: str, returncode: int, timing_ms: int = 0):
        self._out = (stdout, stderr, returncode, timing_ms)

    def run(self, workspace_path: Path, command: list[str], timeout_seconds: float):
        return self._out


def test_build_runner_returns_ok_when_lake_succeeds() -> None:
    """When runner returns 0, BuildRunner returns ok=True."""
    mock = _MockRunner("out", "", 0, 10)
    runner = BuildRunner(timeout_seconds=5.0, runner=mock)
    result = runner.run(Path("/tmp/ws"))
    assert result.ok is True
    assert result.command == ["lake", "build"]
    assert result.stdout == "out"
    assert result.stderr == ""
    assert result.timing_ms == 10


def test_build_runner_returns_not_ok_when_lake_fails() -> None:
    """When runner returns non-zero, BuildRunner returns ok=False."""
    mock = _MockRunner("", "error", 1)
    runner = BuildRunner(timeout_seconds=5.0, runner=mock)
    result = runner.run(Path("/tmp/ws"))
    assert result.ok is False
    assert result.stderr == "error"


def test_build_runner_handles_os_error() -> None:
    """When runner returns -1 (e.g. OSError), BuildRunner returns ok=False with stderr."""
    mock = _MockRunner("", "lake not found", -1)
    runner = BuildRunner(timeout_seconds=5.0, runner=mock)
    result = runner.run(Path("/tmp/ws"))
    assert result.ok is False
    assert "lake" in result.stderr or "not found" in result.stderr


def test_build_runner_handles_timeout() -> None:
    """When runner returns -1 with timeout message, BuildRunner returns ok=False."""
    mock = _MockRunner("", "Run exceeded 5s", -1, 5000)
    runner = BuildRunner(timeout_seconds=5.0, runner=mock)
    result = runner.run(Path("/tmp/ws"))
    assert result.ok is False
    assert "exceeded" in result.stderr or "5" in result.stderr
