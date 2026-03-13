#!/usr/bin/env python3
"""Run the main demo: scenarios 1, 2, 3 in order (good patch, sorry patch, protected path + review).

Scenario 1: clean patch -> accepted.
Scenario 2: sorry patch -> rejected.
Scenario 3: protected path -> needs_review -> (CLI resume or --ui-resume for UI).

With --ui-resume: after scenario 3 hits awaiting_approval, print Review UI URL
and instructions; do not call obr resume (user completes in browser).
Without --ui-resume: when CHECKPOINTER=postgres and DATABASE_URL are set,
scenario 3 resumes via CLI and asserts accepted; otherwise scenario 3 skipped.

Skips with exit 0 if Gateway unreachable or fixtures missing.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

THREAD_ID_SCENARIO_3 = "hero-demo-3"
REPO_ID = "lean-mini"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"
STATUS_FAILED = "failed"
STATUS_AWAITING_APPROVAL = "awaiting_approval"
STATUS_AWAITING_REVIEW = "awaiting_review"
MAX_STDOUT_SNIPPET = 400


def _run(
    cli: list[str], cwd: str, env: dict[str, str], timeout: int = 90
) -> subprocess.CompletedProcess:
    """Run CLI subprocess; capture stdout/stderr and enforce timeout."""
    return subprocess.run(
        cli,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _parse_run_output(
    raw: str, context: str
) -> tuple[dict | None, str | None]:
    """Parse JSON from subprocess stdout. Returns (data, error_message)."""
    if not (raw or "").strip():
        return None, f"{context}: empty stdout"
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None, f"{context}: output is not a JSON object"
        return data, None
    except json.JSONDecodeError as e:
        snippet = (raw or "")[:MAX_STDOUT_SNIPPET].replace("\n", " ")
        return None, f"{context}: invalid JSON ({e}). stdout snippet: {snippet!r}"


def _get_fid_and_session(
    repo_root: Path, cli: list[str], cwd: str, env: dict[str, str]
) -> tuple[str | None, str | None]:
    """Open env and create session; return (fingerprint_id, session_id) or (None, None)."""
    fixture = repo_root / "tests" / "integration" / "fixtures" / "lean-mini"
    out = _run(
        cli
        + [
            "open-environment",
            "--repo-id", REPO_ID,
            "--repo-path", str(fixture),
        ],
        cwd=cwd,
        env=env,
        timeout=15,
    )
    if out.returncode != 0:
        return None, None
    data, err = _parse_run_output(out.stdout, "open-environment")
    if err or not data:
        return None, None
    fid = data.get("fingerprint_id")
    if not fid:
        return None, None
    out2 = _run(cli + ["create-session", fid], cwd=cwd, env=env, timeout=10)
    if out2.returncode != 0:
        return fid, None
    data2, _ = _parse_run_output(out2.stdout, "create-session")
    return fid, data2.get("session_id") if data2 else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run hero demo: scenarios 1, 2, 3")
    parser.add_argument(
        "--ui-resume",
        action="store_true",
        help="Scenario 3: print Review UI URL and instructions, do not call obr resume",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Log subprocess and parse steps to stderr",
    )
    args = parser.parse_args()

    log = logging.getLogger("hero_demo")
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
    else:
        log.addHandler(logging.NullHandler())

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
    cli = [sys.executable, "-m", "obligation_runtime_orchestrator.cli"]
    cwd = str(repo_root)

    # --- Scenario 1: clean patch -> accepted ---
    log.debug("Scenario 1: open-environment, create-session, run-patch-obligation")
    fid1, _ = _get_fid_and_session(repo_root, cli, cwd, env)
    if fid1 is None:
        print(
            "Skipped: Gateway not running or open-environment failed",
            file=sys.stderr,
        )
        return 0

    out1 = _run(
        cli
        + [
            "run-patch-obligation",
            "--repo-id", REPO_ID,
            "--repo-path", str(fixture_path),
        ],
        cwd=cwd,
        env=env,
        timeout=60,
    )
    if out1.returncode != 0:
        err = out1.stderr or out1.stdout
        print("Scenario 1 failed: run-patch-obligation", err, file=sys.stderr)
        return 1
    data1, parse_err = _parse_run_output(out1.stdout, "run-patch-obligation (scenario 1)")
    if parse_err:
        print(parse_err, file=sys.stderr)
        return 1
    assert data1 is not None
    if data1.get("status") != STATUS_ACCEPTED:
        got = data1.get("status")
        print(
            f"Scenario 1 failed: expected {STATUS_ACCEPTED!r}, got {got!r}",
            file=sys.stderr,
        )
        return 1
    if data1.get("artifacts_count", 0) < 1:
        print("Scenario 1 failed: expected artifacts_count >= 1", file=sys.stderr)
        return 1
    n_art = data1.get("artifacts_count", 0)
    print("Scenario 1 passed: status=accepted, artifacts_count>=", n_art)

    # --- Scenario 2: sorry patch -> rejected ---
    log.debug("Scenario 2: new session, run-patch-obligation with sorry patch")
    fid2, _ = _get_fid_and_session(repo_root, cli, cwd, env)
    if fid2 is None:
        print("Skipped: create-session for scenario 2 failed", file=sys.stderr)
        return 0

    out2 = _run(
        cli
        + [
            "run-patch-obligation",
            "--repo-id", REPO_ID,
            "--repo-path", str(fixture_path),
            "--patch-file", str(sorry_patch),
            "--patch-apply-path", "Mini/Basic.lean",
            "--target-files", "Mini/Basic.lean",
        ],
        cwd=cwd,
        env=env,
        timeout=90,
    )
    if out2.returncode != 0:
        err = out2.stderr or out2.stdout
        print("Scenario 2 failed: run-patch-obligation", err, file=sys.stderr)
        return 1
    data2, parse_err = _parse_run_output(out2.stdout, "run-patch-obligation (scenario 2)")
    if parse_err:
        print(parse_err, file=sys.stderr)
        return 1
    assert data2 is not None
    status2 = data2.get("status")
    if status2 not in (STATUS_REJECTED, STATUS_FAILED):
        print(
            f"Scenario 2 failed: expected rejected/failed, got {status2!r}",
            file=sys.stderr,
        )
        return 1
    print("Scenario 2 passed: status=", status2)

    # --- Scenario 3: protected path -> review -> resume ---
    if args.ui_resume:
        log.debug("Scenario 3 (ui-resume): run-patch-obligation, then print UI instructions")
        fid3, _ = _get_fid_and_session(repo_root, cli, cwd, env)
        if fid3 is None:
            print("Skipped: create-session for scenario 3 failed", file=sys.stderr)
            return 0
        out3 = _run(
            cli
            + [
                "run-patch-obligation",
                "--thread-id", THREAD_ID_SCENARIO_3,
                "--repo-id", REPO_ID,
                "--repo-path", str(fixture_path),
                "--protected-paths", "Mini/Basic.lean",
            ],
            cwd=cwd,
            env=env,
            timeout=90,
        )
        if out3.returncode != 0:
            err = out3.stderr or out3.stdout
            print("Scenario 3 failed: run-patch-obligation", err, file=sys.stderr)
            return 1
        data3, parse_err = _parse_run_output(
            out3.stdout, "run-patch-obligation (scenario 3)"
        )
        if parse_err:
            print(parse_err, file=sys.stderr)
            return 1
        assert data3 is not None
        status3 = data3.get("status")
        if status3 in (STATUS_AWAITING_APPROVAL, STATUS_AWAITING_REVIEW):
            print("Scenario 3 interrupted for review. Complete in the Review UI:")
            print(f"  1. Open http://localhost:3000/reviews/{THREAD_ID_SCENARIO_3}")
            print("  2. Click Approve (or Reject)")
            print("  3. Click Resume run")
            print("(Requires Gateway with CHECKPOINTER=postgres and DATABASE_URL.)")
            return 0
        if status3 in (STATUS_ACCEPTED, STATUS_REJECTED, STATUS_FAILED):
            print("Scenario 3 passed: status=", status3, "(no review required)")
            return 0
        print(f"Scenario 3 unexpected status {status3!r}", file=sys.stderr)
        return 1

    # Automated resume: requires Postgres
    if os.environ.get("CHECKPOINTER") != "postgres" and not os.environ.get(
        "DATABASE_URL"
    ):
        print(
            "Skipped: scenario 3 with CLI resume requires "
            "CHECKPOINTER=postgres and DATABASE_URL",
            file=sys.stderr,
        )
        print(
            "Scenarios 1 and 2 passed. For full flow (including scenario 3), "
            "set DATABASE_URL and CHECKPOINTER=postgres; see docs/demos/main-demo.md.",
            file=sys.stderr,
        )
        return 0

    log.debug("Scenario 3: run-patch-obligation then obr resume")
    fid3, _ = _get_fid_and_session(repo_root, cli, cwd, env)
    if fid3 is None:
        print("Skipped: create-session for scenario 3 failed", file=sys.stderr)
        return 0

    out3 = _run(
        cli
        + [
            "run-patch-obligation",
            "--thread-id", THREAD_ID_SCENARIO_3,
            "--repo-id", REPO_ID,
            "--repo-path", str(fixture_path),
            "--protected-paths", "Mini/Basic.lean",
        ],
        cwd=cwd,
        env=env,
        timeout=90,
    )
    if out3.returncode != 0:
        err = out3.stderr or out3.stdout
        print("Scenario 3 failed: run-patch-obligation", err, file=sys.stderr)
        return 1
    data3, parse_err = _parse_run_output(
        out3.stdout, "run-patch-obligation (scenario 3)"
    )
    if parse_err:
        print(parse_err, file=sys.stderr)
        return 1
    assert data3 is not None
    status3 = data3.get("status")

    if status3 in (STATUS_AWAITING_APPROVAL, STATUS_AWAITING_REVIEW):
        out4 = _run(
            cli + ["resume", THREAD_ID_SCENARIO_3, "--decision", "approved"],
            cwd=cwd,
            env=env,
            timeout=60,
        )
        if out4.returncode != 0:
            err = out4.stderr or out4.stdout
            print("Scenario 3 failed: resume", err, file=sys.stderr)
            return 1
        data4, _ = _parse_run_output(out4.stdout, "resume")
        if data4:
            status3 = data4.get("status", status3)

    if status3 != STATUS_ACCEPTED:
        print(
            f"Scenario 3 failed: expected {STATUS_ACCEPTED} after resume, got {status3!r}",
            file=sys.stderr,
        )
        return 1
    print("Scenario 3 passed: status=accepted after resume")
    return 0


if __name__ == "__main__":
    sys.exit(main())
