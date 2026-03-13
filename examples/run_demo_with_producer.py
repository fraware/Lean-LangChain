#!/usr/bin/env python3
"""Demo: run patch obligation with an optional producer to fill current_patch.

Usage:
  python examples/run_demo_with_producer.py --producer fixture --repo-path PATH --repo-id ID
  python examples/run_demo_with_producer.py --producer openai --repo-path PATH --repo-id ID  # needs OPENAI_API_KEY
  python examples/run_demo_with_producer.py --producer anthropic --repo-path PATH --repo-id ID  # needs ANTHROPIC_API_KEY

The producer proposes a patch; we set initial state current_patch and invoke the existing graph.
Core verification path is unchanged.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Repo root on path so "examples.*" and orchestrator/SDK resolve when run from anywhere
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _gateway_url() -> str:
    return os.environ.get("OBR_GATEWAY_URL", "http://localhost:8000")


def _get_checkpointer():
    if os.environ.get("CHECKPOINTER") == "postgres" or os.environ.get("DATABASE_URL"):
        uri = os.environ.get("DATABASE_URL")
        if uri:
            try:
                from langgraph.checkpoint.postgres import PostgresSaver
                saver = PostgresSaver.from_conn_string(uri)
                saver.setup()
                return saver
            except ImportError:
                pass
    try:
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
    except ImportError:
        return None


def _resolve_producer(name: str, args: argparse.Namespace):
    if name == "fixture":
        from examples.fixture_patch_producer import FixturePatchProducer
        patch_file = getattr(args, "patch_file", None)
        constant = getattr(args, "constant_patch", None)
        if constant:
            import ast
            try:
                constant = ast.literal_eval(constant)
            except Exception:
                constant = {"Mini/Basic.lean": "def x := 1\n"}
        else:
            constant = {"Mini/Basic.lean": "def x := 1\n"}
        if patch_file:
            return FixturePatchProducer(patch_file=patch_file)
        return FixturePatchProducer(constant_patch=constant)
    if name == "openai":
        from examples.openai_patch_producer import OpenAIPatchProducer
        return OpenAIPatchProducer(model=getattr(args, "model", "gpt-4o-mini"))
    if name == "anthropic":
        from examples.anthropic_patch_producer import AnthropicPatchProducer
        return AnthropicPatchProducer(model=getattr(args, "model", "claude-3-5-haiku-20241022"))
    raise ValueError(f"Unknown producer: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run patch obligation with optional producer")
    parser.add_argument("--producer", choices=["fixture", "openai", "anthropic"], default="fixture")
    parser.add_argument("--repo-path", required=True, help="Path to repo (e.g. tests/integration/fixtures/lean-mini)")
    parser.add_argument("--repo-id", default="lean-mini")
    parser.add_argument("--target-file", action="append", dest="target_files", default=None)
    parser.add_argument("--patch-file", help="For fixture: path to patch file")
    parser.add_argument("--constant-patch", help="For fixture: dict as string e.g. \"{'Mini/Basic.lean': 'def x := 1\\\\n'}\"")
    parser.add_argument("--model", help="Model name for openai/anthropic")
    parser.add_argument("--thread-id", default="demo-thread")
    args = parser.parse_args()

    try:
        from obligation_runtime_orchestrator.runtime.graph import build_patch_admissibility_graph
        from obligation_runtime_orchestrator.runtime.initial_state import make_initial_state
        from obligation_runtime_orchestrator.producer import context_from_state
        from obligation_runtime_sdk.client import ObligationRuntimeClient
    except ImportError as e:
        print(json.dumps({"error": str(e), "status": "failed"}, indent=2))
        return 1

    producer = _resolve_producer(args.producer, args)
    client = ObligationRuntimeClient(base_url=_gateway_url())
    checkpointer = _get_checkpointer()
    graph = build_patch_admissibility_graph(client=client, checkpointer=checkpointer)

    obligation = {"target": {"repo_id": args.repo_id}}
    initial = make_initial_state(
        thread_id=args.thread_id,
        obligation_id="demo-ob",
        obligation=obligation,
        target_files=args.target_files or ["Mini/Basic.lean"],
        repo_path=args.repo_path,
    )

    context = context_from_state(initial)
    patch = producer.propose_patch(context)
    initial["current_patch"] = patch

    config = {"configurable": {"thread_id": initial["thread_id"]}} if checkpointer else None
    result = graph.invoke(initial, config=config) if config else graph.invoke(initial)
    print(json.dumps({
        "status": result.get("status"),
        "artifacts_count": len(result.get("artifacts") or []),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
