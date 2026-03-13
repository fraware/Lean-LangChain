"""Runner abstraction for Lean execution: local, container, or microVM.

Used by BuildRunner, transport, axiom/fresh. Optional pool limits via
OBR_INTERACTIVE_RUNNER_MAX and OBR_BATCH_RUNNER_MAX (semaphore per kind).
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Protocol


class LeanRunner(Protocol):
    """Protocol for running a command in a workspace (local or container)."""

    def run(
        self,
        workspace_path: Path,
        command: list[str],
        timeout_seconds: float,
    ) -> tuple[str, str, int, int]:
        """Run command in workspace. Returns (stdout, stderr, returncode, timing_ms)."""
        ...


class LocalRunner:
    """Run commands via local subprocess. Default for dev and CI."""

    def run(
        self,
        workspace_path: Path,
        command: list[str],
        timeout_seconds: float,
    ) -> tuple[str, str, int, int]:
        workspace_path = Path(workspace_path)
        start = time.perf_counter()
        try:
            result = subprocess.run(
                command,
                cwd=str(workspace_path),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return (
                result.stdout or "",
                result.stderr or "",
                result.returncode,
                elapsed_ms,
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = int(timeout_seconds * 1000)
            return (
                "",
                f"Run exceeded {timeout_seconds}s",
                -1,
                elapsed_ms,
            )
        except OSError as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ("", str(e), -1, elapsed_ms)


def _container_run_args(
    workspace_path: Path,
    image: str,
    command: list[str],
    docker_cmd: str = "docker",
    runtime: str | None = None,
) -> list[str]:
    """Build docker run arguments. Used by ContainerRunner, MicroVMRunner, tests."""
    workspace_path = Path(workspace_path).resolve()
    run_cmd = [docker_cmd, "run"]
    if runtime is not None:
        run_cmd.extend(["--runtime", runtime])
    run_cmd.extend([
        "--rm",
        "--label",
        "obr=1",
        "-v",
        f"{workspace_path}:/workspace",
        "-w",
        "/workspace",
    ])
    network = os.environ.get("OBR_CONTAINER_NETWORK")
    run_cmd.extend(["--network", network if network is not None else "none"])
    memory_mb = os.environ.get("OBR_CONTAINER_MEMORY_MB")
    if memory_mb is not None:
        run_cmd.extend(["--memory", f"{memory_mb}m"])
    cpus = os.environ.get("OBR_CONTAINER_CPUS")
    if cpus is not None:
        run_cmd.extend(["--cpus", str(cpus)])
    run_cmd.append(image)
    run_cmd.extend(command)
    return run_cmd


class ContainerRunner:
    """Run commands inside a container with workspace mounted. Use for isolation."""

    def __init__(
        self,
        image: str | None = None,
        docker_cmd: str = "docker",
    ) -> None:
        self._image = (
            image or os.environ.get("OBR_DOCKER_IMAGE", "lean-worker:latest")
        )
        self._docker_cmd = docker_cmd

    def run(
        self,
        workspace_path: Path,
        command: list[str],
        timeout_seconds: float,
    ) -> tuple[str, str, int, int]:
        workspace_path = Path(workspace_path).resolve()
        start = time.perf_counter()
        run_cmd = _container_run_args(
            workspace_path,
            self._image,
            command,
            self._docker_cmd,
            runtime=None,
        )
        try:
            result = subprocess.run(
                run_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return (
                result.stdout or "",
                result.stderr or "",
                result.returncode,
                elapsed_ms,
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = int(timeout_seconds * 1000)
            return (
                "",
                f"Container run exceeded {timeout_seconds}s",
                -1,
                elapsed_ms,
            )
        except OSError as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ("", str(e), -1, elapsed_ms)


class MicroVMRunner:
    """Run commands in a microVM via gVisor runsc (OCI runtime) or Firecracker.

    runsc: same as ContainerRunner but with docker run --runtime=runsc for
    stronger isolation. Uses OBR_DOCKER_IMAGE (or OBR_MICROVM_IMAGE).
    Firecracker: delegates to an external script (OBR_MICROVM_FIRECRACKER_RUN)
    that starts a microVM, runs the command, and prints JSON result.
    """

    def __init__(
        self,
        image: str | None = None,
        docker_cmd: str = "docker",
        runtime: str = "runsc",
    ) -> None:
        self._image = (
            image
            or os.environ.get("OBR_MICROVM_IMAGE")
            or os.environ.get("OBR_DOCKER_IMAGE", "lean-worker:latest")
        )
        self._docker_cmd = docker_cmd
        self._runtime = runtime

    def run(
        self,
        workspace_path: Path,
        command: list[str],
        timeout_seconds: float,
    ) -> tuple[str, str, int, int]:
        workspace_path = Path(workspace_path).resolve()
        start = time.perf_counter()
        run_cmd = _container_run_args(
            workspace_path,
            self._image,
            command,
            self._docker_cmd,
            runtime=self._runtime,
        )
        try:
            result = subprocess.run(
                run_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return (
                result.stdout or "",
                result.stderr or "",
                result.returncode,
                elapsed_ms,
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = int(timeout_seconds * 1000)
            return (
                "",
                f"MicroVM run exceeded {timeout_seconds}s",
                -1,
                elapsed_ms,
            )
        except OSError as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ("", str(e), -1, elapsed_ms)


class FirecrackerRunner:
    """Run commands via an external Firecracker helper script.

    Script (OBR_MICROVM_FIRECRACKER_RUN) is invoked with:
      script_path workspace_path timeout_seconds cmd_arg1 cmd_arg2 ...
    and must print one JSON object to stdout:
      {"stdout": "...", "stderr": "...", "returncode": int}
    script_path may be str (single executable) or list[str] (e.g. [python, script.py]).
    """

    def __init__(self, script_path: str | list[str]) -> None:
        self._script = script_path

    def run(
        self,
        workspace_path: Path,
        command: list[str],
        timeout_seconds: float,
    ) -> tuple[str, str, int, int]:
        workspace_path = Path(workspace_path).resolve()
        start = time.perf_counter()
        base = [self._script] if isinstance(self._script, str) else list(self._script)
        argv = base + [
            str(workspace_path),
            str(int(timeout_seconds)),
            *command,
        ]
        try:
            result = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=timeout_seconds + 10,
                cwd=str(workspace_path),
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
        except subprocess.TimeoutExpired:
            elapsed_ms = int(timeout_seconds * 1000)
            return (
                "",
                "Firecracker script exceeded timeout",
                -1,
                elapsed_ms,
            )
        except OSError as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ("", str(e), -1, elapsed_ms)
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        if result.returncode != 0:
            return (out, err or "Firecracker script failed", result.returncode, elapsed_ms)
        try:
            data: dict[str, Any] = json.loads(out)
            return (
                data.get("stdout", ""),
                data.get("stderr", ""),
                int(data.get("returncode", -1)),
                elapsed_ms,
            )
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            return (
                out,
                f"Invalid script output: {e}",
                -1,
                elapsed_ms,
            )


def _microvm_runner(kind: str) -> LeanRunner:
    """Return MicroVMRunner or FirecrackerRunner based on OBR_MICROVM_RUNTIME."""
    runtime = (os.environ.get("OBR_MICROVM_RUNTIME") or "runsc").strip().lower()
    if runtime == "firecracker":
        script = os.environ.get("OBR_MICROVM_FIRECRACKER_RUN")
        if not script:
            raise RuntimeError(
                "OBR_MICROVM_RUNTIME=firecracker requires OBR_MICROVM_FIRECRACKER_RUN"
            )
        return FirecrackerRunner(script_path=script)
    image = os.environ.get("OBR_MICROVM_IMAGE") or os.environ.get("OBR_DOCKER_IMAGE")
    if kind == "interactive":
        image = image or os.environ.get("OBR_INTERACTIVE_DOCKER_IMAGE") or "lean-worker:latest"
    else:
        image = image or "lean-worker:latest"
    return MicroVMRunner(image=image, runtime=runtime)


class _PoolLimitedRunner:
    """Wraps a LeanRunner and limits concurrent run() calls with a semaphore."""

    def __init__(self, inner: LeanRunner, max_concurrent: int) -> None:
        self._inner = inner
        self._semaphore = threading.Semaphore(max_concurrent)

    def run(
        self,
        workspace_path: Path,
        command: list[str],
        timeout_seconds: float,
    ) -> tuple[str, str, int, int]:
        self._semaphore.acquire()
        try:
            return self._inner.run(workspace_path, command, timeout_seconds)
        finally:
            self._semaphore.release()


def _maybe_pool_limit(runner: LeanRunner, kind: str) -> LeanRunner:
    """Wrap runner with PoolLimitedRunner when OBR_*_RUNNER_MAX is set."""
    env_key = "OBR_INTERACTIVE_RUNNER_MAX" if kind == "interactive" else "OBR_BATCH_RUNNER_MAX"
    raw = os.environ.get(env_key, "").strip()
    if not raw:
        return runner
    try:
        max_concurrent = int(raw)
    except ValueError:
        return runner
    if max_concurrent < 1:
        return runner
    return _PoolLimitedRunner(runner, max_concurrent)


def get_runner(kind: str = "batch") -> LeanRunner:
    """Return runner for interactive or batch lane.

    kind: "interactive" | "batch". Uses OBR_INTERACTIVE_RUNNER / OBR_BATCH_RUNNER
    (default "local"); if "container", uses ContainerRunner; if "microvm", uses
    MicroVMRunner (runsc) or FirecrackerRunner. Fallback: OBR_WORKER_RUNNER.
    When OBR_INTERACTIVE_RUNNER_MAX or OBR_BATCH_RUNNER_MAX is set (positive int),
    wraps the runner in a semaphore-limited pool so at most N runs are concurrent.
    """
    inner: LeanRunner
    if kind == "interactive":
        runner_env = os.environ.get("OBR_INTERACTIVE_RUNNER") or os.environ.get(
            "OBR_WORKER_RUNNER", "local"
        )
        if runner_env == "container":
            image = os.environ.get("OBR_INTERACTIVE_DOCKER_IMAGE") or os.environ.get(
                "OBR_DOCKER_IMAGE", "lean-worker:latest"
            )
            inner = ContainerRunner(image=image)
        elif runner_env == "microvm":
            inner = _microvm_runner("interactive")
        else:
            inner = LocalRunner()
    else:
        runner_env = os.environ.get("OBR_BATCH_RUNNER") or os.environ.get(
            "OBR_WORKER_RUNNER", "local"
        )
        if runner_env == "container":
            image = os.environ.get("OBR_DOCKER_IMAGE", "lean-worker:latest")
            inner = ContainerRunner(image=image)
        elif runner_env == "microvm":
            inner = _microvm_runner("batch")
        else:
            inner = LocalRunner()
    return _maybe_pool_limit(inner, kind)
