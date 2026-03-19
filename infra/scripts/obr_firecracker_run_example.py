#!/usr/bin/env python3
"""Example Firecracker helper script for OBR_MICROVM_FIRECRACKER_RUN.

Contract: argv = [script, workspace_path, timeout_seconds, cmd_arg1, cmd_arg2, ...]
Output: single JSON line to stdout: {"stdout": "...", "stderr": "...", "returncode": N}

This example runs the command in a subprocess (same host). Replace with your own
script that starts a Firecracker microVM, mounts/syncs the workspace, runs the
command inside the VM, and prints the same JSON.
"""

from __future__ import annotations

import json
import subprocess
import sys


def main() -> None:
    if len(sys.argv) < 4:
        print(
            json.dumps(
                {
                    "stdout": "",
                    "stderr": "Usage: script workspace_path timeout_seconds cmd...",
                    "returncode": -1,
                }
            )
        )
        sys.exit(0)
    workspace_path = sys.argv[1]
    try:
        timeout_seconds = int(sys.argv[2])
    except ValueError:
        print(
            json.dumps(
                {
                    "stdout": "",
                    "stderr": "Invalid timeout_seconds",
                    "returncode": -1,
                }
            )
        )
        sys.exit(0)
    command = sys.argv[3:]
    if not command:
        print(
            json.dumps(
                {
                    "stdout": "",
                    "stderr": "No command provided",
                    "returncode": -1,
                }
            )
        )
        sys.exit(0)
    try:
        result = subprocess.run(
            command,
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        out = json.dumps(
            {
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "returncode": result.returncode,
            }
        )
        print(out)
    except subprocess.TimeoutExpired:
        print(
            json.dumps(
                {
                    "stdout": "",
                    "stderr": f"Command exceeded {timeout_seconds}s",
                    "returncode": -1,
                }
            )
        )
        sys.exit(0)
    except OSError as e:
        print(
            json.dumps(
                {
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1,
                }
            )
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
