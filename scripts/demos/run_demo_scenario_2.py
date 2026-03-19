#!/usr/bin/env python3
"""Run demo scenario 2 (patch with sorry => rejected) against a live Gateway via CLI. Skips if Gateway unreachable."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    fixture_path = repo_root / "tests" / "integration" / "fixtures" / "lean-mini"
    sorry_patch = repo_root / "scripts" / "fixtures" / "sorry_patch.lean"
    if not fixture_path.is_dir():
        print("Skipped: fixture path not found", file=sys.stderr)
        return 0
    if not sorry_patch.is_file():
        print("Skipped: sorry_patch.lean not found", file=sys.stderr)
        return 0

    env = os.environ.copy()
    env.setdefault("OBR_GATEWAY_URL", "http://localhost:8000")
    cli = [sys.executable, "-m", "lean_langchain_orchestrator.cli"]
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

    if not (out.stdout or "").strip():
        print("Skipped: empty stdout from open-environment", file=sys.stderr)
        return 0
    try:
        data = json.loads(out.stdout)
        if not isinstance(data, dict):
            print("Skipped: open-environment output is not a JSON object", file=sys.stderr)
            return 0
        fid = data.get("fingerprint_id")
        if not fid:
            print("Skipped: no fingerprint_id in output", file=sys.stderr)
            return 0
    except json.JSONDecodeError as e:
        print(f"Skipped: invalid JSON from open-environment: {e}", file=sys.stderr)
        return 0

    out2 = subprocess.run(
        cli + ["create-session", fid], cwd=cwd, env=env, capture_output=True, text=True, timeout=10
    )
    if out2.returncode != 0:
        print("Skipped: create-session failed", file=sys.stderr)
        return 0

    out3 = subprocess.run(
        cli
        + [
            "run-patch-obligation",
            "--repo-id",
            "lean-mini",
            "--repo-path",
            str(fixture_path),
            "--patch-file",
            str(sorry_patch),
            "--patch-apply-path",
            "Mini/Basic.lean",
            "--target-files",
            "Mini/Basic.lean",
        ],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    if out3.returncode != 0:
        print("run-patch-obligation failed:", out3.stderr or out3.stdout, file=sys.stderr)
        return 1

    if not (out3.stdout or "").strip():
        print("run-patch-obligation produced empty stdout", file=sys.stderr)
        return 1
    try:
        data3 = json.loads(out3.stdout)
        if not isinstance(data3, dict):
            print("run-patch-obligation output is not a JSON object", file=sys.stderr)
            return 1
        status = data3.get("status")
        if status not in ("rejected", "failed"):
            print(f"Expected status rejected or failed, got {status!r}", file=sys.stderr)
            return 1
    except json.JSONDecodeError as e:
        print(f"Invalid JSON from run-patch-obligation: {e}", file=sys.stderr)
        return 1

    print("Scenario 2 passed: status=", status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
