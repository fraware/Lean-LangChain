"""Hardening tests: read-only base, writable overlay, session cleanup, timeout."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from obligation_runtime_lean_gateway.server.leak_check import list_obr_containers
from obligation_runtime_lean_gateway.server.runner import (
    _container_run_args,
    ContainerRunner,
    FirecrackerRunner,
    MicroVMRunner,
    get_runner,
)
from obligation_runtime_lean_gateway.server.session_manager import (
    SessionLease,
    SessionManager,
)
from obligation_runtime_lean_gateway.server.worker_runner import run_with_timeout


def test_run_with_timeout_aborts_on_expiry() -> None:
    """run_with_timeout raises TimeoutError when fn exceeds limit."""
    def slow() -> str:
        time.sleep(2.0)
        return "done"

    with pytest.raises(TimeoutError, match="exceeded"):
        run_with_timeout(slow, timeout_seconds=0.1)


def test_run_with_timeout_returns_result_when_quick() -> None:
    """run_with_timeout returns fn result when fn finishes within limit."""
    result = run_with_timeout(lambda: 42, timeout_seconds=5.0)
    assert result == 42


def test_session_release_removes_lease() -> None:
    """SessionManager.release removes the session so get raises."""
    mgr = SessionManager()
    lease = SessionLease(
        session_id="s1",
        fingerprint_id="fp1",
        workspace_path=Path("/tmp/x"),
        started_at=0.0,
        last_used_at=0.0,
    )
    mgr.register(lease)
    assert mgr.get("s1").session_id == "s1"
    mgr.release("s1")
    with pytest.raises(KeyError):
        mgr.get("s1")


def test_container_run_args_defaults() -> None:
    """_container_run_args produces docker run with volume, workspace, and --network none."""
    with patch.dict(os.environ, {}, clear=False):
        env_key = "OBR_CONTAINER_NETWORK"
        env_backup = os.environ.pop(env_key, None)
        try:
            args = _container_run_args(Path("/ws"), "img:latest", ["lake", "build"])
        finally:
            if env_backup is not None:
                os.environ[env_key] = env_backup
    assert args[0] == "docker"
    assert "run" in args
    assert "--rm" in args
    assert "--label" in args
    assert "obr=1" in args
    assert "-v" in args
    assert any("/workspace" in str(a) for a in args)
    assert "-w" in args
    idx_net = args.index("--network")
    assert args[idx_net + 1] == "none"
    assert "img:latest" in args
    assert "lake" in args
    assert "build" in args


def test_container_run_args_with_network_bridge() -> None:
    """When OBR_CONTAINER_NETWORK=bridge, docker run gets --network bridge."""
    with patch.dict(os.environ, {"OBR_CONTAINER_NETWORK": "bridge"}, clear=False):
        args = _container_run_args(Path("/ws"), "img", ["lake", "build"])
    assert "--network" in args
    idx = args.index("--network")
    assert args[idx + 1] == "bridge"


def test_container_run_args_with_memory_and_cpus() -> None:
    """When OBR_CONTAINER_MEMORY_MB and OBR_CONTAINER_CPUS set, docker run gets limits."""
    with patch.dict(
        os.environ,
        {"OBR_CONTAINER_MEMORY_MB": "512", "OBR_CONTAINER_CPUS": "1.5"},
        clear=False,
    ):
        args = _container_run_args(Path("/ws"), "img", ["lake", "build"])
    assert "--memory" in args
    assert "512m" in args
    assert "--cpus" in args
    assert "1.5" in args


def test_container_run_args_with_runtime_runsc() -> None:
    """_container_run_args with runtime=runsc adds --runtime runsc."""
    args = _container_run_args(
        Path("/ws"), "img", ["lake", "build"], runtime="runsc"
    )
    idx = args.index("--runtime")
    assert args[idx + 1] == "runsc"
    assert "run" in args
    assert "img" in args


def test_microvm_runner_runsc_builds_docker_with_runtime() -> None:
    """_container_run_args with runtime=runsc produces --runtime runsc (used by MicroVMRunner)."""
    args = _container_run_args(
        Path("/ws"), "lean:test", ["lake", "build"], runtime="runsc"
    )
    assert "--runtime" in args
    assert "runsc" in args


def test_get_runner_microvm_returns_microvm_runner() -> None:
    """When OBR_WORKER_RUNNER=microvm and OBR_MICROVM_RUNTIME=runsc, get_runner returns MicroVMRunner."""
    with patch.dict(
        os.environ,
        {
            "OBR_WORKER_RUNNER": "microvm",
            "OBR_BATCH_RUNNER": "microvm",
            "OBR_MICROVM_RUNTIME": "runsc",
        },
        clear=False,
    ):
        r = get_runner("batch")
    assert isinstance(r, MicroVMRunner)


def test_get_runner_microvm_firecracker_requires_script() -> None:
    """When OBR_MICROVM_RUNTIME=firecracker without OBR_MICROVM_FIRECRACKER_RUN, get_runner raises."""
    with patch.dict(
        os.environ,
        {
            "OBR_WORKER_RUNNER": "microvm",
            "OBR_BATCH_RUNNER": "microvm",
            "OBR_MICROVM_RUNTIME": "firecracker",
        },
        clear=False,
    ):
        saved = os.environ.pop("OBR_MICROVM_FIRECRACKER_RUN", None)
        try:
            with pytest.raises(RuntimeError, match="OBR_MICROVM_FIRECRACKER_RUN"):
                get_runner("batch")
        finally:
            if saved is not None:
                os.environ["OBR_MICROVM_FIRECRACKER_RUN"] = saved


def test_get_runner_microvm_firecracker_returns_firecracker_runner() -> None:
    """When OBR_MICROVM_RUNTIME=firecracker and script set, get_runner returns FirecrackerRunner."""
    with patch.dict(
        os.environ,
        {
            "OBR_WORKER_RUNNER": "microvm",
            "OBR_BATCH_RUNNER": "microvm",
            "OBR_MICROVM_RUNTIME": "firecracker",
            "OBR_MICROVM_FIRECRACKER_RUN": "/usr/bin/obr-firecracker-run",
        },
        clear=False,
    ):
        r = get_runner("batch")
    assert isinstance(r, FirecrackerRunner)


def test_firecracker_runner_parses_json_output(tmp_path: Path) -> None:
    """FirecrackerRunner runs script and parses JSON stdout into (stdout, stderr, returncode)."""
    import sys
    script = tmp_path / "fake_runner.py"
    script.write_text(
        "import sys, json\n"
        "d = {\"stdout\": \"hello\", \"stderr\": \"warn\", \"returncode\": 0}\n"
        "print(json.dumps(d))\n"
    )
    runner = FirecrackerRunner(
        script_path=[sys.executable, str(script)]
    )
    out, err, code, _ = runner.run(
        tmp_path, ["echo", "hi"], timeout_seconds=10.0
    )
    assert out == "hello"
    assert err == "warn"
    assert code == 0


def test_firecracker_runner_script_failure_returns_stderr(tmp_path: Path) -> None:
    """When script exits non-zero, FirecrackerRunner returns script stderr."""
    import sys
    script = tmp_path / "fail.py"
    script.write_text(
        "import sys\n"
        "print('not json', file=sys.stderr)\n"
        "sys.exit(1)\n"
    )
    runner = FirecrackerRunner(script_path=[sys.executable, str(script)])
    _, err, code, _ = runner.run(tmp_path, ["true"], timeout_seconds=5.0)
    assert code == 1
    assert "not json" in err or "Firecracker script failed" in err


@pytest.mark.skipif(not shutil.which("docker"), reason="docker not in PATH")
def test_container_runner_no_leftover_container_after_run() -> None:
    """After ContainerRunner.run() completes, no leftover container with same image (--rm behavior)."""
    workspace = Path(__file__).resolve().parent / ".." / "integration" / "fixtures" / "lean-mini"
    workspace = workspace.resolve()
    if not workspace.is_dir():
        pytest.skip("lean-mini fixture not found")
    image = os.environ.get("OBR_DOCKER_IMAGE", "lean-worker:latest")
    runner = ContainerRunner(image=image)
    try:
        runner.run(workspace, ["lake", "build"], timeout_seconds=60.0)
    except Exception:
        pytest.skip("Container run failed (image may not exist or lake not in image)")
    try:
        out = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"ancestor={image}", "--format", "{{.ID}}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        pytest.skip("docker ps timed out (Docker daemon slow or busy)")
    if out.returncode != 0:
        pytest.skip("docker ps -a failed")
    ids = [x.strip() for x in (out.stdout or "").strip().splitlines() if x.strip()]
    assert len(ids) == 0, f"Expected no leftover containers for image {image}; found: {ids}"
    obr_ids = list_obr_containers()
    assert isinstance(obr_ids, list), "list_obr_containers must return a list"
    assert len(obr_ids) == 0, f"Expected no OBR-labeled containers after run; found: {obr_ids}"


def test_list_obr_containers_returns_list() -> None:
    """list_obr_containers returns a list (empty when docker unavailable or no matches)."""
    result = list_obr_containers()
    assert isinstance(result, list)
    assert all(isinstance(cid, str) for cid in result)
