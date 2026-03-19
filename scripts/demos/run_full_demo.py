#!/usr/bin/env python3
"""Run the full demo: proof-preserving patch gate (6 steps).

Step 1: No patch -> accepted (baseline).
Step 2: Valid proof edit -> accepted.
Step 3: Sorry patch -> rejected.
Step 4: False theorem -> rejected (build fails).
Step 5a: Protected path -> approve -> resume -> accepted.
Step 5b: Protected path -> reject -> resume -> rejected.
Step 6: Export evidence bundle for the approved run.

Steps 5a, 5b, 6 require CHECKPOINTER=postgres and DATABASE_URL; else skipped (exit 0).
With --ui-resume: after step 5a hits awaiting_approval, print Review UI URL and exit.
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

REPO_ID = "lean-mini"
THREAD_ID_5A = "full-demo-5a"
THREAD_ID_5B = "full-demo-5b"
ARTIFACTS_OUTPUT = "full_demo_witness.json"
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


def _parse_run_output(raw: str, context: str) -> tuple[dict | None, str | None]:
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
        return None, f"{context}: invalid JSON ({e}). snippet: {snippet!r}"


def _get_fid_and_session(
    repo_root: Path, cli: list[str], cwd: str, env: dict[str, str]
) -> tuple[str | None, str | None]:
    """Open env and create session; return (fingerprint_id, session_id) or (None, None)."""
    fixture = repo_root / "tests" / "integration" / "fixtures" / "lean-mini"
    out = _run(
        cli
        + [
            "open-environment",
            "--repo-id",
            REPO_ID,
            "--repo-path",
            str(fixture),
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
    parser = argparse.ArgumentParser(
        description="Run full demo: proof-preserving patch gate (6 steps)"
    )
    parser.add_argument(
        "--ui-resume",
        action="store_true",
        help="After step 5a awaiting_approval, print Review UI URL and exit (no 5b/6)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Log subprocess and parse steps to stderr",
    )
    args = parser.parse_args()

    log = logging.getLogger("full_demo")
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
    else:
        log.addHandler(logging.NullHandler())

    repo_root = Path(__file__).resolve().parent.parent.parent
    fixture_path = repo_root / "tests" / "integration" / "fixtures" / "lean-mini"
    sorry_patch = repo_root / "scripts" / "fixtures" / "sorry_patch.lean"
    valid_edit_patch = repo_root / "scripts" / "fixtures" / "valid_proof_edit_patch.lean"
    false_theorem_patch = repo_root / "scripts" / "fixtures" / "false_theorem_patch.lean"

    if not fixture_path.is_dir():
        print("Skipped: fixture path not found", file=sys.stderr)
        return 0
    if not sorry_patch.is_file():
        print("Skipped: sorry_patch.lean not found", file=sys.stderr)
        return 0
    if not valid_edit_patch.is_file():
        print("Skipped: valid_proof_edit_patch.lean not found", file=sys.stderr)
        return 0
    if not false_theorem_patch.is_file():
        print("Skipped: false_theorem_patch.lean not found", file=sys.stderr)
        return 0

    env = os.environ.copy()
    env.setdefault("OBR_GATEWAY_URL", "http://localhost:8000")
    cli = [sys.executable, "-m", "obligation_runtime_orchestrator.cli"]
    cwd = str(repo_root)

    # --- Step 1: No patch (baseline) -> accepted ---
    log.debug("Step 1: open-environment, create-session, run-patch-obligation")
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
            "--repo-id",
            REPO_ID,
            "--repo-path",
            str(fixture_path),
        ],
        cwd=cwd,
        env=env,
        timeout=60,
    )
    if out1.returncode != 0:
        print(
            "Step 1 failed: run-patch-obligation",
            out1.stderr or out1.stdout,
            file=sys.stderr,
        )
        return 1
    data1, parse_err = _parse_run_output(out1.stdout, "run-patch-obligation (step 1)")
    if parse_err:
        print(parse_err, file=sys.stderr)
        return 1
    assert data1 is not None
    if data1.get("status") != STATUS_ACCEPTED:
        print(
            f"Step 1 failed: expected {STATUS_ACCEPTED!r}, got " f"{data1.get('status')!r}",
            file=sys.stderr,
        )
        return 1
    if data1.get("artifacts_count", 0) < 1:
        print("Step 1 failed: expected artifacts_count >= 1", file=sys.stderr)
        return 1
    print(
        "Step 1 passed: no patch accepted, artifacts_count>=",
        data1.get("artifacts_count", 0),
    )

    # --- Step 2: Valid proof edit -> accepted ---
    log.debug("Step 2: run-patch-obligation with valid_proof_edit_patch.lean")
    fid2, _ = _get_fid_and_session(repo_root, cli, cwd, env)
    if fid2 is None:
        print("Step 2 failed: create-session failed", file=sys.stderr)
        return 1

    out2 = _run(
        cli
        + [
            "run-patch-obligation",
            "--repo-id",
            REPO_ID,
            "--repo-path",
            str(fixture_path),
            "--patch-file",
            str(valid_edit_patch),
            "--patch-apply-path",
            "Mini/Basic.lean",
            "--target-files",
            "Mini/Basic.lean",
        ],
        cwd=cwd,
        env=env,
        timeout=90,
    )
    if out2.returncode != 0:
        print(
            "Step 2 failed: run-patch-obligation",
            out2.stderr or out2.stdout,
            file=sys.stderr,
        )
        return 1
    data2, parse_err = _parse_run_output(out2.stdout, "run-patch-obligation (step 2)")
    if parse_err:
        print(parse_err, file=sys.stderr)
        return 1
    assert data2 is not None
    if data2.get("status") != STATUS_ACCEPTED:
        print(
            f"Step 2 failed: expected {STATUS_ACCEPTED!r}, got " f"{data2.get('status')!r}",
            file=sys.stderr,
        )
        return 1
    if data2.get("artifacts_count", 0) < 1:
        print("Step 2 failed: expected artifacts_count >= 1", file=sys.stderr)
        return 1
    print("Step 2 passed: valid proof edit accepted")

    # --- Step 3: Sorry patch -> rejected ---
    log.debug("Step 3: run-patch-obligation with sorry_patch.lean")
    fid3, _ = _get_fid_and_session(repo_root, cli, cwd, env)
    if fid3 is None:
        print("Step 3 failed: create-session failed", file=sys.stderr)
        return 1

    out3 = _run(
        cli
        + [
            "run-patch-obligation",
            "--repo-id",
            REPO_ID,
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
        timeout=90,
    )
    if out3.returncode != 0:
        print(
            "Step 3 failed: run-patch-obligation",
            out3.stderr or out3.stdout,
            file=sys.stderr,
        )
        return 1
    data3, parse_err = _parse_run_output(out3.stdout, "run-patch-obligation (step 3)")
    if parse_err:
        print(parse_err, file=sys.stderr)
        return 1
    assert data3 is not None
    status3 = data3.get("status")
    if status3 not in (STATUS_REJECTED, STATUS_FAILED):
        print(
            f"Step 3 failed: expected rejected/failed, got {status3!r}",
            file=sys.stderr,
        )
        return 1
    print("Step 3 passed: sorry patch rejected")

    # --- Step 4: False theorem -> rejected ---
    log.debug("Step 4: run-patch-obligation with false_theorem_patch.lean")
    fid4, _ = _get_fid_and_session(repo_root, cli, cwd, env)
    if fid4 is None:
        print("Step 4 failed: create-session failed", file=sys.stderr)
        return 1

    out4 = _run(
        cli
        + [
            "run-patch-obligation",
            "--repo-id",
            REPO_ID,
            "--repo-path",
            str(fixture_path),
            "--patch-file",
            str(false_theorem_patch),
            "--patch-apply-path",
            "Mini/Basic.lean",
            "--target-files",
            "Mini/Basic.lean",
        ],
        cwd=cwd,
        env=env,
        timeout=90,
    )
    if out4.returncode != 0:
        print(
            "Step 4 failed: run-patch-obligation",
            out4.stderr or out4.stdout,
            file=sys.stderr,
        )
        return 1
    data4, parse_err = _parse_run_output(out4.stdout, "run-patch-obligation (step 4)")
    if parse_err:
        print(parse_err, file=sys.stderr)
        return 1
    assert data4 is not None
    status4 = data4.get("status")
    if status4 not in (STATUS_REJECTED, STATUS_FAILED):
        print(
            f"Step 4 failed: expected rejected/failed, got {status4!r}",
            file=sys.stderr,
        )
        return 1
    print("Step 4 passed: false theorem rejected")

    # --- Steps 5a, 5b, 6 require Postgres checkpointer ---
    need_pg = os.environ.get("CHECKPOINTER") != "postgres" or not os.environ.get("DATABASE_URL")
    if need_pg:
        print(
            "Skipped: steps 5-6 require CHECKPOINTER=postgres and DATABASE_URL",
            file=sys.stderr,
        )
        print(
            "Steps 1-4 passed. For full flow set DATABASE_URL and "
            "CHECKPOINTER=postgres; see docs/demos/full-demo.md.",
            file=sys.stderr,
        )
        return 0

    # --- Step 5a: Protected path -> approve -> resume -> accepted ---
    log.debug("Step 5a: run-patch-obligation protected path, resume approved")
    fid5a, _ = _get_fid_and_session(repo_root, cli, cwd, env)
    if fid5a is None:
        print("Step 5a failed: create-session failed", file=sys.stderr)
        return 1

    out5a = _run(
        cli
        + [
            "run-patch-obligation",
            "--thread-id",
            THREAD_ID_5A,
            "--repo-id",
            REPO_ID,
            "--repo-path",
            str(fixture_path),
            "--protected-paths",
            "Mini/Basic.lean",
        ],
        cwd=cwd,
        env=env,
        timeout=90,
    )
    if out5a.returncode != 0:
        print(
            "Step 5a failed: run-patch-obligation",
            out5a.stderr or out5a.stdout,
            file=sys.stderr,
        )
        return 1
    data5a, parse_err = _parse_run_output(out5a.stdout, "run-patch-obligation (step 5a)")
    if parse_err:
        print(parse_err, file=sys.stderr)
        return 1
    assert data5a is not None
    status5a = data5a.get("status")

    if status5a in (STATUS_AWAITING_APPROVAL, STATUS_AWAITING_REVIEW):
        if args.ui_resume:
            print("Step 5a interrupted for review. Complete in the Review UI:")
            print(f"  1. Open http://localhost:3000/reviews/{THREAD_ID_5A}")
            print("  2. Click Approve (or Reject)")
            print("  3. Click Resume run")
            print("(Steps 5b and 6 are skipped when using --ui-resume.)")
            return 0

        out_resume = _run(
            cli + ["resume", THREAD_ID_5A, "--decision", "approved"],
            cwd=cwd,
            env=env,
            timeout=60,
        )
        if out_resume.returncode != 0:
            print(
                "Step 5a failed: resume",
                out_resume.stderr or out_resume.stdout,
                file=sys.stderr,
            )
            return 1
        data_resume, _ = _parse_run_output(out_resume.stdout, "resume (step 5a)")
        if data_resume:
            status5a = data_resume.get("status", status5a)

    if status5a != STATUS_ACCEPTED:
        print(
            f"Step 5a failed: expected {STATUS_ACCEPTED} after resume, " f"got {status5a!r}",
            file=sys.stderr,
        )
        return 1
    print("Step 5a passed: protected path approved, run accepted")

    # --- Step 5b: Protected path -> reject -> resume -> rejected ---
    log.debug("Step 5b: run-patch-obligation protected path, resume rejected")
    fid5b, _ = _get_fid_and_session(repo_root, cli, cwd, env)
    if fid5b is None:
        print("Step 5b failed: create-session failed", file=sys.stderr)
        return 1

    out5b = _run(
        cli
        + [
            "run-patch-obligation",
            "--thread-id",
            THREAD_ID_5B,
            "--repo-id",
            REPO_ID,
            "--repo-path",
            str(fixture_path),
            "--protected-paths",
            "Mini/Basic.lean",
        ],
        cwd=cwd,
        env=env,
        timeout=90,
    )
    if out5b.returncode != 0:
        print(
            "Step 5b failed: run-patch-obligation",
            out5b.stderr or out5b.stdout,
            file=sys.stderr,
        )
        return 1
    data5b, parse_err = _parse_run_output(out5b.stdout, "run-patch-obligation (step 5b)")
    if parse_err:
        print(parse_err, file=sys.stderr)
        return 1
    assert data5b is not None
    status5b = data5b.get("status")

    if status5b in (STATUS_AWAITING_APPROVAL, STATUS_AWAITING_REVIEW):
        out_resume_b = _run(
            cli + ["resume", THREAD_ID_5B, "--decision", "rejected"],
            cwd=cwd,
            env=env,
            timeout=60,
        )
        if out_resume_b.returncode != 0:
            print(
                "Step 5b failed: resume",
                out_resume_b.stderr or out_resume_b.stdout,
                file=sys.stderr,
            )
            return 1
        data_resume_b, _ = _parse_run_output(out_resume_b.stdout, "resume (step 5b)")
        if data_resume_b:
            status5b = data_resume_b.get("status", status5b)

    if status5b != STATUS_REJECTED:
        print(
            f"Step 5b failed: expected {STATUS_REJECTED} after resume, " f"got {status5b!r}",
            file=sys.stderr,
        )
        return 1
    print("Step 5b passed: protected path rejected by human")

    # --- Step 6: Export evidence bundle ---
    log.debug("Step 6: obr artifacts --thread-id full-demo-5a --output ...")
    output_path = repo_root / ARTIFACTS_OUTPUT
    out6 = _run(
        cli
        + [
            "artifacts",
            "--thread-id",
            THREAD_ID_5A,
            "--output",
            str(output_path),
        ],
        cwd=cwd,
        env=env,
        timeout=15,
    )
    if out6.returncode != 0:
        print(
            "Step 6 failed: artifacts",
            out6.stderr or out6.stdout,
            file=sys.stderr,
        )
        return 1
    if not output_path.is_file():
        print("Step 6 failed: artifacts output file not created", file=sys.stderr)
        return 1
    raw = output_path.read_text(encoding="utf-8")
    try:
        artifacts = json.loads(raw)
    except json.JSONDecodeError as e:
        print(
            f"Step 6 failed: invalid JSON in artifacts file: {e}",
            file=sys.stderr,
        )
        return 1
    if not isinstance(artifacts, list) or len(artifacts) < 1:
        print(
            "Step 6 failed: expected at least one artifact (witness_bundle)",
            file=sys.stderr,
        )
        return 1
    has_witness = any(isinstance(a, dict) and a.get("kind") == "witness_bundle" for a in artifacts)
    if not has_witness:
        print(
            "Step 6 failed: no witness_bundle in artifacts",
            file=sys.stderr,
        )
        return 1
    print("Step 6 passed: evidence bundle exported to", output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
