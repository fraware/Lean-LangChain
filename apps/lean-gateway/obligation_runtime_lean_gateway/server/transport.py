"""Transport boundary for Lean integration. The interactive lane talks to this interface; no raw LSP/subprocess output is exposed above it."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from .session_manager import SessionManager

if TYPE_CHECKING:
    from .runner import LeanRunner


class LeanTransport(Protocol):
    """
    Interface for running Lean checks in a session workspace.
    Implementations may use LSP, headless Lean, or a test double (injected only in tests).
    The gateway never exposes raw LSP wire format; all results go through the normalizer.
    Optional: get_goal, hover, definition for LSP-backed transports.
    """

    def check(self, session_id: str, file_path: str) -> tuple[list[dict], list[dict], bool]:
        """
        Run an interactive check on the given file in the session workspace.
        Returns (raw_diagnostics, raw_goals, ok).
        Raw dicts are normalized by InteractiveNormalizer before being returned to clients.
        """
        ...


def transport_get_goal(
    transport: LeanTransport,
    session_id: str,
    file_path: str,
    line: int,
    column: int,
    goal_kind: str = "plainGoal",
) -> list[dict]:
    """Return goals from transport if it implements get_goal; else empty list."""
    if hasattr(transport, "get_goal"):
        return getattr(transport, "get_goal")(session_id, file_path, line, column, goal_kind)
    return []


def transport_hover(
    transport: LeanTransport,
    session_id: str,
    file_path: str,
    line: int,
    column: int,
) -> str:
    """Return hover contents from transport if it implements hover; else empty string."""
    if hasattr(transport, "hover"):
        return getattr(transport, "hover")(session_id, file_path, line, column)
    return ""


def transport_definition(
    transport: LeanTransport,
    session_id: str,
    file_path: str,
    line: int,
    column: int,
) -> list[dict]:
    """Return definition locations from transport if it implements definition; else empty list."""
    if hasattr(transport, "definition"):
        return getattr(transport, "definition")(session_id, file_path, line, column)
    return []


class TestDoubleTransport:
    """Test double for interactive Lean; returns empty diagnostics/goals and ok=True. Inject only in tests via deps.set_test_transport(); production requires SubprocessLeanTransport or LspLeanTransport."""

    def check(self, session_id: str, file_path: str) -> tuple[list[dict], list[dict], bool]:
        return ([], [], True)


class SubprocessLeanTransport:
    """Runs `lake build` in the session workspace; returns ([], [], ok). Enable via OBR_USE_REAL_LEAN=1."""

    def __init__(
        self,
        session_manager: SessionManager,
        timeout_seconds: float = 300.0,
        runner: LeanRunner | None = None,
    ) -> None:
        from .runner import get_runner
        self._session_manager = session_manager
        self._timeout_seconds = timeout_seconds
        self._runner = runner if runner is not None else get_runner("interactive")

    def check(self, session_id: str, file_path: str) -> tuple[list[dict], list[dict], bool]:
        lease = self._session_manager.get(session_id)
        workspace_path = Path(lease.workspace_path)
        _, stderr, returncode, _ = self._runner.run(
            workspace_path,
            ["lake", "build"],
            self._timeout_seconds,
        )
        ok = returncode == 0
        if not ok and stderr:
            return ([{"message": stderr}], [], ok)
        return ([], [], ok)


class LspLeanTransport:
    """
    Lean 4 LSP over stdio: real diagnostics and goals. Enable via OBR_USE_LEAN_LSP=1.
    Runs `lean --server` in the session workspace; communicates via JSON-RPC with Content-Length framing.
    """

    def __init__(
        self,
        session_manager: SessionManager,
        timeout_seconds: float = 300.0,
    ) -> None:
        self._session_manager = session_manager
        self._timeout_seconds = timeout_seconds

    def check(self, session_id: str, file_path: str) -> tuple[list[dict], list[dict], bool]:
        from .lsp_client import run_check

        lease = self._session_manager.get(session_id)
        workspace_path = Path(lease.workspace_path)
        full_path = workspace_path / file_path
        diagnostics, goals, ok = run_check(
            workspace_path,
            full_path,
            timeout_seconds=self._timeout_seconds,
        )
        return (diagnostics, goals, ok)

    def get_goal(
        self,
        session_id: str,
        file_path: str,
        line: int,
        column: int,
        goal_kind: str = "plainGoal",
    ) -> list[dict]:
        from .lsp_client import run_get_goal

        lease = self._session_manager.get(session_id)
        workspace_path = Path(lease.workspace_path)
        return run_get_goal(workspace_path, file_path, line, column, goal_kind, self._timeout_seconds)

    def hover(self, session_id: str, file_path: str, line: int, column: int) -> str:
        from .lsp_client import run_hover

        lease = self._session_manager.get(session_id)
        workspace_path = Path(lease.workspace_path)
        return run_hover(workspace_path, file_path, line, column, self._timeout_seconds)

    def definition(self, session_id: str, file_path: str, line: int, column: int) -> list[dict]:
        from .lsp_client import run_definition

        lease = self._session_manager.get(session_id)
        workspace_path = Path(lease.workspace_path)
        return run_definition(workspace_path, file_path, line, column, self._timeout_seconds)
