"""Integration tests for protocol obligation handoff_legality: events and evaluator."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from obligation_runtime_policy.pack_loader import load_pack
from obligation_runtime_policy.protocol_evaluator import evaluate_protocol_obligation

HANDOFF_GOOD_EVENTS = [
    {"kind": "claim", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}},
    {"kind": "delegate", "event_id": "e2", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}, "prior_event_ids": ["e1"]},
]

HANDOFF_BAD_OWNER_EVENTS = [
    {"kind": "claim", "event_id": "e1", "actor": {"agent_id": "alice", "role": "owner"}, "task": {"task_id": "t1", "task_class": "patch"}},
    {"kind": "delegate", "event_id": "e2", "actor": {"agent_id": "bob", "role": "other"}, "task": {"task_id": "t1", "task_class": "patch"}, "prior_event_ids": ["e1"]},
]


def test_handoff_legality_good_events_accepted() -> None:
    """Protocol handoff_legality with same-owner events returns accepted."""
    pack = load_pack("single_owner_handoff_v1")
    result = evaluate_protocol_obligation("handoff_legality", HANDOFF_GOOD_EVENTS, pack)
    assert result.decision == "accepted"
    assert result.trust_level == "clean"


def test_handoff_legality_bad_owner_rejected() -> None:
    """Protocol handoff_legality with different-owner delegate returns rejected."""
    pack = load_pack("single_owner_handoff_v1")
    result = evaluate_protocol_obligation("handoff_legality", HANDOFF_BAD_OWNER_EVENTS, pack)
    assert result.decision == "rejected"
    assert "owner_mismatch" in result.reasons


def test_run_protocol_obligation_cli_events_file() -> None:
    """run-protocol-obligation CLI with --events-file returns expected JSON decision. Skips if orchestrator not installed."""
    import subprocess
    import sys
    repo_root = Path(__file__).resolve().parent.parent.parent
    cli = [sys.executable, "-m", "obligation_runtime_orchestrator.cli"]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(HANDOFF_GOOD_EVENTS, f)
        events_file = f.name
    try:
        out = subprocess.run(
            cli + ["run-protocol-obligation", "--obligation-class", "handoff_legality", "--pack", "single_owner_handoff_v1", "--events-file", events_file],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if out.returncode != 0 and "ModuleNotFoundError" in (out.stderr or ""):
            pytest.skip("orchestrator not installed (run make install-dev-full)")
        assert out.returncode == 0
        data = json.loads(out.stdout)
        assert data.get("decision") == "accepted"
    finally:
        Path(events_file).unlink(missing_ok=True)
