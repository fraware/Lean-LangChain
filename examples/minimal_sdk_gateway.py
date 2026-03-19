#!/usr/bin/env python3
"""Minimal example: call the Obligation Runtime Gateway from the Python SDK.

Run a Gateway first (e.g. uvicorn lean_langchain_gateway.api.app:app),
then from repo root:

  python examples/minimal_sdk_gateway.py
  python examples/minimal_sdk_gateway.py --repo-path /path/to/lean-repo

Opens an environment, creates a session, runs batch-verify. Uses the SDK
context manager, timeouts, and structured error handling.
For full demos see docs/demos/ and make demo-core, make demo-full.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

LOG = logging.getLogger("minimal_sdk_gateway")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Minimal SDK call to a running Obligation Runtime Gateway",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OBR_GATEWAY_URL", "http://localhost:8000"),
        help="Gateway base URL",
    )
    parser.add_argument(
        "--repo-path",
        default="",
        help="Path to a Lean repo (default: tests/integration/fixtures/lean-mini)",
    )
    parser.add_argument(
        "--repo-id",
        default="lean-mini",
        help="Repo id for open_environment",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Request timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--batch-timeout",
        type=float,
        default=120.0,
        help="Batch-verify timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    repo_path = args.repo_path or str(
        _REPO_ROOT / "tests" / "integration" / "fixtures" / "lean-mini"
    )
    if not os.path.isdir(repo_path):
        LOG.error("Repo path not found: %s. Pass --repo-path.", repo_path)
        return 1

    try:
        from lean_langchain_sdk import (
            ObligationRuntimeAPIError,
            ObligationRuntimeClient,
        )
    except ImportError as e:
        LOG.error("SDK not installed: %s", e)
        return 1

    try:
        with ObligationRuntimeClient(
            base_url=args.base_url,
            timeout=args.timeout,
            batch_verify_timeout=args.batch_timeout,
        ) as client:
            LOG.info("Opening environment repo_id=%s path=%s", args.repo_id, repo_path)
            open_data = client.open_environment(
                repo_id=args.repo_id,
                repo_path=repo_path,
                commit_sha="head",
            )
            fingerprint_id = open_data.fingerprint_id
            if not fingerprint_id:
                LOG.error("No fingerprint_id in response: %s", open_data)
                return 1
            LOG.info("Environment opened: fingerprint_id=%s", fingerprint_id)

            session_data = client.create_session(fingerprint_id=fingerprint_id)
            session_id = session_data.session_id
            if not session_id:
                LOG.error("No session_id in response: %s", session_data)
                return 1
            LOG.info("Session created: session_id=%s", session_id)

            target_files = ["Mini/Basic.lean"] if "lean-mini" in repo_path else ["Main.lean"]
            LOG.info("Running batch_verify target_files=%s", target_files)
            batch_data = client.batch_verify(
                session_id=session_id,
                target_files=target_files,
                target_declarations=[],
            )
            ok = batch_data.ok
            trust_level = batch_data.trust_level
            LOG.info("batch_verify: ok=%s trust_level=%s", ok, trust_level)
            return 0

    except ObligationRuntimeAPIError as e:
        LOG.error(
            "Gateway error [%s] %s: %s",
            e.status_code,
            e.code,
            e.message,
        )
        if e.body:
            LOG.debug("Response body: %s", e.body)
        return 1
    except Exception as e:
        LOG.error("Request failed: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
