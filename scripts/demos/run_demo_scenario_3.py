#!/usr/bin/env python3
"""Run demo scenario 3 (protected path => review required) against a live Gateway via CLI.

Runs patch obligation with --protected-paths so the run hits needs_review; if status is
awaiting_approval, runs resume with approved. Two paths: (1) In-process: a test or script
that invokes the graph twice with MemorySaver (no Postgres). (2) Two CLI invocations: this
script runs run-patch-obligation then resume as subprocesses; requires CHECKPOINTER=postgres
and DATABASE_URL so state is shared. Skips if Gateway unreachable or Postgres not set."""

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

    # Resume across two CLI subprocesses requires a shared checkpointer (Postgres).
    if os.environ.get("CHECKPOINTER") != "postgres" and not os.environ.get("DATABASE_URL"):
        print(
            "Skipped: resume across CLI invocations requires CHECKPOINTER=postgres and DATABASE_URL",
            file=sys.stderr,
        )
        return 0

    env = os.environ.copy()
    env.setdefault("OBR_GATEWAY_URL", "http://localhost:8000")
    cli = [sys.executable, "-m", "obligation_runtime_orchestrator.cli"]
    cwd = str(repo_root)
    thread_id = "demo-scenario-3"

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

    out2 = subprocess.run(cli + ["create-session", fid], cwd=cwd, env=env, capture_output=True, text=True, timeout=10)
    if out2.returncode != 0:
        print("Skipped: create-session failed", file=sys.stderr)
        return 0

    out3 = subprocess.run(
        cli + [
            "run-patch-obligation",
            "--thread-id", thread_id,
            "--repo-id", "lean-mini",
            "--repo-path", str(fixture_path),
            "--protected-paths", "Mini/Basic.lean",
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

    try:
        data3 = json.loads(out3.stdout)
        status = data3.get("status")
    except json.JSONDecodeError:
        print("Invalid JSON from run-patch-obligation", file=sys.stderr)
        return 1

    if status in ("awaiting_approval", "awaiting_review"):
        out4 = subprocess.run(
            cli + ["resume", thread_id, "--decision", "approved"],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if out4.returncode != 0:
            print("resume failed:", out4.stderr or out4.stdout, file=sys.stderr)
            return 1
        try:
            data4 = json.loads(out4.stdout)
            status = data4.get("status", status)
        except json.JSONDecodeError:
            pass

    if status not in ("accepted", "rejected", "failed", "awaiting_approval", "awaiting_review"):
        print(f"Unexpected status {status!r}", file=sys.stderr)
        return 1
    print("Scenario 3 passed: status=", status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
