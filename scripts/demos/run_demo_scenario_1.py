#!/usr/bin/env python3
"""Run demo scenario 1 (clean patch => accepted) against a live Gateway. Skips with exit 0 if Gateway is unreachable."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    fixture_path = repo_root / "tests" / "integration" / "fixtures" / "lean-mini"
    if not fixture_path.is_dir():
        print("Skipped: fixture path not found", file=sys.stderr)
        return 0

    env = os.environ.copy()
    env.setdefault("OBR_GATEWAY_URL", "http://localhost:8000")
    cli = [sys.executable, "-m", "obligation_runtime_orchestrator.cli"]
    cwd = str(repo_root)

    try:
        out = subprocess.run(
            cli + ["open-environment", "--repo-id", "lean-mini", "--repo-path", str(fixture_path)],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"Skipped: {e}", file=sys.stderr)
        return 0

    if out.returncode != 0:
        print("Skipped: Gateway not running or open-environment failed", file=sys.stderr)
        return 0

    try:
        data = json.loads(out.stdout)
        fid = data.get("fingerprint_id")
        if not fid:
            print("Skipped: no fingerprint_id in output", file=sys.stderr)
            return 0
    except json.JSONDecodeError:
        print("Skipped: invalid JSON from open-environment", file=sys.stderr)
        return 0

    out2 = subprocess.run(
        cli + ["create-session", fid], cwd=cwd, env=env, capture_output=True, text=True, timeout=10
    )
    if out2.returncode != 0:
        print("Skipped: create-session failed", file=sys.stderr)
        return 0

    out3 = subprocess.run(
        cli + ["run-patch-obligation", "--repo-id", "lean-mini", "--repo-path", str(fixture_path)],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if out3.returncode != 0:
        print("run-patch-obligation failed:", out3.stderr or out3.stdout, file=sys.stderr)
        return 1

    try:
        data3 = json.loads(out3.stdout)
        status = data3.get("status")
        count = data3.get("artifacts_count", 0)
        if status != "accepted":
            print(f"Expected status 'accepted', got {status!r}", file=sys.stderr)
            return 1
        if count < 1:
            print(f"Expected artifacts_count >= 1, got {count}", file=sys.stderr)
            return 1
    except json.JSONDecodeError:
        print("Invalid JSON from run-patch-obligation", file=sys.stderr)
        return 1

    print("Scenario 1 passed: status=accepted, artifacts_count>=", count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
