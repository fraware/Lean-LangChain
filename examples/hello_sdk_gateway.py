#!/usr/bin/env python3
"""Minimal example: call the Obligation Runtime Gateway from the Python SDK.

Run a Gateway first (e.g. uvicorn obligation_runtime_lean_gateway.api.app:app),
then from repo root:

  python examples/hello_sdk_gateway.py
  python examples/hello_sdk_gateway.py --repo-path /path/to/lean-repo

This script opens an environment, creates a session, and optionally runs batch-verify.
Use it as a copy-paste starting point for Tier 2 reusers (API client only).
"""

from __future__ import annotations

import argparse
import os
import sys

# Repo root on path so orchestrator/SDK resolve when run from anywhere
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal SDK call to a running Gateway")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OBR_GATEWAY_URL", "http://localhost:8000"),
        help="Gateway base URL",
    )
    parser.add_argument(
        "--repo-path",
        default="",
        help="Path to a Lean repo (optional; used for open_environment and batch_verify)",
    )
    parser.add_argument(
        "--repo-id",
        default="lean-mini",
        help="Repo id for open_environment",
    )
    args = parser.parse_args()

    from obligation_runtime_sdk import ObligationRuntimeClient

    client = ObligationRuntimeClient(base_url=args.base_url)

    repo_path = args.repo_path or os.path.join(_REPO_ROOT, "tests", "integration", "fixtures", "lean-mini")
    if not os.path.isdir(repo_path):
        print(f"Repo path not found: {repo_path}. Pass --repo-path or run from repo with fixtures.")
        return 1

    open_data = client.open_environment(
        repo_id=args.repo_id,
        repo_path=repo_path,
        commit_sha="head",
    )
    print("open_environment:", open_data.get("fingerprint_id", open_data))

    session_data = client.create_session(fingerprint_id=open_data["fingerprint_id"])
    session_id = session_data["session_id"]
    print("create_session:", session_id)

    batch_data = client.batch_verify(
        session_id=session_id,
        target_files=["Mini/Basic.lean"] if "lean-mini" in repo_path else ["Main.lean"],
        target_declarations=[],
    )
    print("batch_verify:", batch_data.get("ok"), batch_data.get("trust_level", batch_data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
