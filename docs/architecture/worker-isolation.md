# Worker isolation

Lean workers can run on the host (LocalRunner), in a container (ContainerRunner), or in a microVM (MicroVMRunner). See [runtime-graph.md](runtime-graph.md) and [gateway-api.md](gateway-api.md).

## Overview

Lean execution (build, axiom audit, fresh check, interactive lane when using subprocess transport) can run on the host via subprocess (**LocalRunner**), inside an isolated container (**ContainerRunner**), or in a microVM (**MicroVMRunner** / **FirecrackerRunner**). Isolation ensures that untrusted or third-party code in the workspace cannot escape the execution environment or consume unbounded resources.

## Current implementation

### Runner abstraction

- **Protocol:** [LeanRunner](apps/lean-gateway/lean_langchain_gateway/server/runner.py) in `apps/lean-gateway/.../server/runner.py` defines `run(workspace_path, command, timeout_seconds)` returning `(stdout, stderr, returncode, timing_ms)`.
- **LocalRunner:** Runs commands via subprocess on the host. Default for development and CI when `OBR_WORKER_RUNNER` is not set to `container` or `microvm`. Wall-clock timeout is enforced by `subprocess.run(..., timeout=timeout_seconds)`.
- **ContainerRunner:** Runs `docker run --rm -v <workspace>:/workspace -w /workspace <image> <command>`. The workspace is mounted read-write so that `lake build` and tools can write build artifacts; the host view of the workspace is the same as the container view (no separate overlay in the current design). Enable with `OBR_WORKER_RUNNER=container` and optionally `OBR_DOCKER_IMAGE` (default: `lean-worker:latest`).
- **MicroVMRunner (runsc):** Runs the same OCI image as the container runner but with `docker run --runtime=runsc`, using [gVisor runsc](https://gvisor.dev/) for stronger isolation (user-space kernel). Enable with `OBR_WORKER_RUNNER=microvm` and `OBR_MICROVM_RUNTIME=runsc` (default). Uses `OBR_DOCKER_IMAGE` or `OBR_MICROVM_IMAGE`. Requires Docker configured with the runsc runtime (e.g. add runsc to `/etc/docker/daemon.json`).
- **FirecrackerRunner:** Delegates to an external script (`OBR_MICROVM_FIRECRACKER_RUN`) that starts a Firecracker microVM, runs the command (workspace mounted or synced per script), and prints one JSON line to stdout: `{"stdout": "...", "stderr": "...", "returncode": N}`. Enable with `OBR_WORKER_RUNNER=microvm` and `OBR_MICROVM_RUNTIME=firecracker`; the script path is required.

### Image

- **Default (Lean-capable):** [infra/docker/lean-worker.Dockerfile](infra/docker/lean-worker.Dockerfile) uses `leanprovercommunity/lean4:latest`; `lake` and `lean` are in PATH. Build from repo root: `docker build -f infra/docker/lean-worker.Dockerfile -t lean-worker:test .` (or use `lean-worker-lean4.Dockerfile`, which is equivalent).
- **Slim (no Lean):** [infra/docker/lean-worker-slim.Dockerfile](infra/docker/lean-worker-slim.Dockerfile) is a minimal Python image without Lean; use when workers only run Python entrypoints or when you provide Lean via a custom image.

### Base snapshot and overlay (session workspace)

- **Base snapshot:** The environment fingerprint identifies a specific repo and commit. The Gateway does not clone repos; it assumes the caller has already prepared the workspace (e.g. at `repo_path`). That directory is the “base” content for the session.
- **Overlay (read-only base):** When the Gateway uses OverlayFS, the base snapshot is copied into the environment store and then made **read-only via chmod** (no write bits on files and directories). Only the session overlay work path is writable (and is explicitly made writable after copy so patches can be applied). For stricter isolation (e.g. production), operators can place the base directory on a read-only mount or use an overlayfs with a read-only lower layer. When a session applies a patch via `apply-patch`, the Gateway applies the patch to a session-scoped workspace. Implementations may use a writable overlay (e.g. overlayfs or copy-on-write) so that the base directory remains read-only and only the session’s view is writable. If the code path runs without OverlayFS (e.g. direct workspace path), the base is not guaranteed read-only; for production, use overlay so the base remains unchanged.
- **Code path without OverlayFS:** If the Gateway uses a direct workspace path (no overlay created), the base is not read-only; recommend overlay for production.
- **Cleanup:** When a session is released, the session manager drops the lease; any session-scoped overlay or temporary files should be cleaned up by the implementation (e.g. unmount overlay, delete temp copy). The Gateway’s session manager does not itself manage overlay lifecycle; that is left to the deployment.

## Hardening controls

### Timeout (wall-clock)

- **Enforced:** LocalRunner, ContainerRunner, MicroVMRunner, and FirecrackerRunner use a wall-clock timeout (seconds). For the Gateway, timeouts are configured via `OBR_BUILD_TIMEOUT`, axiom audit timeout via `OBR_AXIOM_AUDIT_TIMEOUT`, and similar env vars. The runner’s `run(..., timeout_seconds=...)` is always called with a finite value; subprocess or container/microVM run is interrupted on expiry.

### Network

- **Container / MicroVM (runsc):** The container and runsc runners default to `--network=none` (no network access). Set `OBR_CONTAINER_NETWORK=bridge` (or `host`, or a custom network name) if the run needs network (e.g. Lake fetching dependencies). When unset, the Gateway runs with `--network=none`.
- **LocalRunner:** No network isolation; the process uses the host network. For production isolation, use ContainerRunner or MicroVMRunner (network is disabled by default).

### CPU and memory limits (container)

- **Optional:** Set `OBR_CONTAINER_MEMORY_MB` and/or `OBR_CONTAINER_CPUS` to pass `--memory=<value>m` and `--cpus=<value>` to `docker run`. If unset, the container has no resource limits (host defaults). **Production:** Enforce these in production for both worker containers and the Gateway container (e.g. via docker-compose `deploy.resources.limits` or Kubernetes resource limits) to avoid a single run exhausting the host.

### Separate worker classes (interactive vs batch)

- **Current (limitation):** The same runner (LocalRunner, ContainerRunner, or MicroVMRunner) is used for batch commands (build, axiom audit, fresh check) and, when applicable, for subprocess-based interactive execution. There is no separate “interactive worker” vs “batch worker” process pool; each invocation is a fresh subprocess or container/microVM run.
- **Pool limits (implemented):** **OBR_INTERACTIVE_RUNNER_MAX** and **OBR_BATCH_RUNNER_MAX** (positive integer) cap concurrent runs per runner kind via a semaphore in `get_runner()`; see **docs/running.md**. Separate pools for interactive vs batch with different limits or images are supported; leak detection (container list check) is in CI (container job).

### Cleanup and leak detection

- **Container:** Each run uses `docker run --rm --label obr=1`, so the container is removed when the command exits and all OBR-started containers are tagged for querying. Use [leak_check.list_obr_containers](apps/lean-gateway/lean_langchain_gateway/server/leak_check.py) to list any OBR-labeled containers (e.g. after tests); the **container** CI job runs a leak-check step that fails the job if any such containers remain after the container runner test.
- **Local subprocess:** Subprocess is started and waited on; no orphan processes from the runner itself. Any child processes left by the command (e.g. a stuck Lean process) are not reaped by the Gateway; operators should set timeouts and, if needed, use cgroups or container runs to guarantee cleanup.
- **Sessions:** SessionManager tracks leases; releasing a session does not by itself kill any running Lean process. Ensure runs are always bound by timeout so that resources are released.

## What is enforced vs left to the image/orchestrator

| Control            | Enforced by Gateway                         | Left to image / orchestrator        |
|--------------------|---------------------------------------------|-------------------------------------|
| Wall-clock timeout | Yes (subprocess/container timeout)          | —                                   |
| Network            | Default `--network=none`; set `OBR_CONTAINER_NETWORK` for access | —                                   |
| Memory limit       | Optional (`OBR_CONTAINER_MEMORY_MB`)        | No limit if unset                   |
| CPU limit          | Optional (`OBR_CONTAINER_CPUS`)             | No limit if unset                   |
| Read-only base     | Documented; overlay is deployment-specific  | Overlay implementation              |
| Cleanup            | `--rm` for container; session release       | Orphan process handling on host     |

## MicroVM workers

MicroVM-based workers are implemented and selectable via `OBR_WORKER_RUNNER=microvm`.

- **runsc (gVisor):** Default when `OBR_MICROVM_RUNTIME` is unset or `runsc`. Uses the same OCI image as the container runner (`OBR_DOCKER_IMAGE` or `OBR_MICROVM_IMAGE`) with `docker run --runtime=runsc`. Provides stronger isolation than plain containers via gVisor’s user-space kernel. Docker must be configured with the runsc runtime (see [gVisor install](https://gvisor.dev/docs/user_guide/install/)).
- **Firecracker:** Set `OBR_MICROVM_RUNTIME=firecracker` and `OBR_MICROVM_FIRECRACKER_RUN` to the path of a helper script. The script is invoked as `script_path workspace_path timeout_seconds cmd_arg1 cmd_arg2 ...` and must print a single JSON object to stdout: `{"stdout": "...", "stderr": "...", "returncode": N}`. The script is responsible for starting a Firecracker microVM (or equivalent), mounting or syncing the workspace, running the command, and returning the result. This keeps Firecracker-specific setup (kernel, rootfs, 9p vs block devices) outside the Gateway. An example script that runs the command in a subprocess (for testing or as a template) is [infra/scripts/obr_firecracker_run_example.py](../../infra/scripts/obr_firecracker_run_example.py); replace with your own invoker for real Firecracker.

Same `LeanRunner` contract: `run(workspace_path, command, timeout_seconds)` returning `(stdout, stderr, returncode, timing_ms)`. Resource limits for runsc use the same env vars as container (`OBR_CONTAINER_MEMORY_MB`, `OBR_CONTAINER_CPUS`).

## CI and testing

- **container:** The CI job sets `OBR_WORKER_RUNNER=container` and `OBR_DOCKER_IMAGE=lean-worker:test`, builds the Lean 4 image, and runs the acceptance lane batch-verify test. This validates that the container runner executes and returns the expected result shape.
- **MicroVM:** With `OBR_WORKER_RUNNER=microvm` and Docker (and optionally runsc) configured, `test_acceptance_lane_microvm_runner_batch_verify` runs batch-verify via the microVM runner; skipped otherwise.
- **Unit tests:** [tests/unit/test_worker_isolation.py](tests/unit/test_worker_isolation.py) cover timeout, session release, container and microVM runner options (network default `none`, optional `bridge`; memory, cpus; runsc runtime; FirecrackerRunner script contract). Optional test `test_container_runner_no_leftover_container_after_run` runs a container command and asserts no leftover container with the same image after the run (validates `--rm`); skipped when Docker is not in PATH.

## Future work

- **Dedicated interactive vs batch pools:** Separate limits or queues for interactive vs batch to avoid head-of-line blocking.
- **Overlay lifecycle:** First-class support for read-only base + per-session writable overlay in the Gateway, with explicit cleanup on session release.

**See also:** [runtime-graph.md](runtime-graph.md), [gateway-api.md](gateway-api.md), [running.md](../running.md).
