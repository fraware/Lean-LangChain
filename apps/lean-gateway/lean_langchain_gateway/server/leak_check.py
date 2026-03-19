"""Optional leak detection for OBR containers.

Containers started by ContainerRunner use --label obr=1 so they can be
queried. Use list_obr_containers() after tests or cleanup to assert no orphans.
"""

from __future__ import annotations

import subprocess

OBR_LABEL = "obr=1"


def list_obr_containers(docker_cmd: str = "docker") -> list[str]:
    """List container IDs that have label obr=1 (all states, including exited).

    Returns list of container IDs. If docker is unavailable or the command fails,
    returns empty list.
    """
    try:
        result = subprocess.run(
            [docker_cmd, "ps", "-a", "--filter", f"label={OBR_LABEL}", "--format", "{{.ID}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []
        return [cid.strip() for cid in (result.stdout or "").strip().splitlines() if cid.strip()]
    except (OSError, subprocess.TimeoutExpired):
        return []
