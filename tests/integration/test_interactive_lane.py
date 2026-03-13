from pathlib import Path

from obligation_runtime_lean_gateway.server.interactive_api import InteractiveAPI
from obligation_runtime_lean_gateway.server.session_manager import SessionManager
from obligation_runtime_lean_gateway.server.transport import TestDoubleTransport
from obligation_runtime_lean_gateway.server.worker_pool import WorkerPool


def test_open_session_and_check(tmp_path: Path) -> None:
    api = InteractiveAPI(SessionManager(), WorkerPool(), transport=TestDoubleTransport())
    session = api.open_session(session_id="sess1", fingerprint_id="fp1", workspace_path=tmp_path)
    result = api.check_interactive(session_id=session.session_id, file_path="Mini/Basic.lean")
    assert result.phase == "interactive"
    assert isinstance(result.ok, bool)
