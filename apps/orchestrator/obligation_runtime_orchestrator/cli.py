"""Obligation Runtime CLI: obr open-environment, create-session, run-patch-obligation, review, artifacts, regressions."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path as PathLib
from typing import Any


def _gateway_url() -> str:
    return os.environ.get("OBR_GATEWAY_URL", "http://localhost:8000")


def _client():
    from obligation_runtime_sdk.client import ObligationRuntimeClient

    return ObligationRuntimeClient(base_url=_gateway_url())


def cmd_open_environment(args: argparse.Namespace) -> int:
    client = _client()
    out = client.open_environment(
        repo_id=args.repo_id,
        repo_path=args.repo_path or None,
        repo_url=args.repo_url or None,
        commit_sha=args.commit_sha or "HEAD",
    )
    print(json.dumps(out, indent=2))
    return 0


def cmd_create_session(args: argparse.Namespace) -> int:
    client = _client()
    out = client.create_session(fingerprint_id=args.fingerprint_id)
    print(json.dumps(out, indent=2))
    return 0


def _get_checkpointer():
    """Return PostgresSaver when CHECKPOINTER=postgres and DATABASE_URL set, else MemorySaver if available."""
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


def cmd_run_patch_obligation(args: argparse.Namespace) -> int:
    try:
        from obligation_runtime_orchestrator.runtime.graph import build_patch_admissibility_graph
        from obligation_runtime_orchestrator.runtime.initial_state import make_initial_state
    except ImportError:
        print(json.dumps({"error": "langgraph not installed", "status": "failed"}, indent=2))
        return 1
    client = _client()
    checkpointer = _get_checkpointer()
    graph = build_patch_admissibility_graph(client=client, checkpointer=checkpointer)
    obligation = {"target": {"repo_id": args.repo_id or "default"}}
    if getattr(args, "protected_paths", None):
        obligation.setdefault("policy", {})["protected_paths"] = args.protected_paths
    initial = make_initial_state(
        thread_id=args.thread_id or "cli-thread",
        obligation_id=args.obligation_id or "cli-ob",
        obligation=obligation,
        target_files=args.target_files or ["Main.lean"],
        target_declarations=args.target_declarations or [],
        repo_path=args.repo_path or "",
        policy_pack_name=getattr(args, "policy_pack", None),
    )
    if getattr(args, "protocol_events_file", None):
        try:
            with open(args.protocol_events_file, encoding="utf-8") as f:
                initial["protocol_events"] = json.load(f)
        except Exception as e:
            print(json.dumps({"error": str(e), "status": "failed"}, indent=2))
            return 1
    if getattr(args, "patch_file", None):
        try:
            with open(args.patch_file, encoding="utf-8") as f:
                content = f.read()
            key = (
                getattr(args, "patch_apply_path", None)
                or PathLib(args.patch_file).name
                or "Main.lean"
            )
            initial["current_patch"] = {key: content}
        except Exception as e:
            print(json.dumps({"error": str(e), "status": "failed"}, indent=2))
            return 1
    config = {"configurable": {"thread_id": initial["thread_id"]}} if checkpointer else None
    result = graph.invoke(initial, config=config) if config else graph.invoke(initial)
    print(
        json.dumps(
            {"status": result.get("status"), "artifacts_count": len(result.get("artifacts") or [])},
            indent=2,
        )
    )
    return 0


def cmd_run_protocol_obligation(args: argparse.Namespace) -> int:
    from obligation_runtime_policy.pack_loader import load_pack
    from obligation_runtime_policy.protocol_evaluator import evaluate_protocol_obligation

    events = []
    if getattr(args, "events_file", None):
        with open(args.events_file, encoding="utf-8") as f:
            events = json.load(f)
    pack = load_pack(args.pack or "single_owner_handoff_v1")
    decision = evaluate_protocol_obligation(
        args.obligation_class or "handoff_legality", events, pack
    )
    print(json.dumps(decision.model_dump(mode="json"), indent=2))
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    if args.open_browser:
        url = f"{_gateway_url().rstrip('/')}/docs"
        try:
            import webbrowser

            webbrowser.open(url)
        except Exception:
            pass
        return 0
    thread_id = getattr(args, "thread_id", None) or ""
    if not thread_id:
        print(json.dumps({"error": "thread_id required for review payload"}, indent=2))
        return 1
    client = _client()
    try:
        payload = client.get_review_payload(thread_id)
        print(json.dumps(payload, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return 1


def cmd_resume(args: argparse.Namespace) -> int:
    """Resume a run after human approval; uses same thread_id and checkpointer so graph continues from checkpoint."""
    try:
        from obligation_runtime_orchestrator.runtime.graph import build_patch_admissibility_graph
        from obligation_runtime_orchestrator.runtime.initial_state import make_resume_state
    except ImportError:
        print(json.dumps({"error": "langgraph not installed", "status": "failed"}, indent=2))
        return 1
    thread_id = getattr(args, "thread_id", None) or ""
    decision = (getattr(args, "decision", None) or "approved").strip().lower()
    if decision not in ("approved", "rejected"):
        decision = "approved"
    if not thread_id:
        print(json.dumps({"error": "thread_id required for resume"}, indent=2))
        return 1
    client = _client()
    checkpointer = _get_checkpointer()
    graph = build_patch_admissibility_graph(client=client, checkpointer=checkpointer)
    resume_state = make_resume_state(thread_id=thread_id, decision=decision)
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(resume_state, config=config)
    print(
        json.dumps(
            {"status": result.get("status"), "artifacts_count": len(result.get("artifacts") or [])},
            indent=2,
        )
    )
    return 0


def cmd_artifacts(args: argparse.Namespace) -> int:
    """Export or list artifacts for a thread from the checkpoint state."""
    thread_id = getattr(args, "thread_id", None) or ""
    if not thread_id:
        print(json.dumps({"error": "thread_id required for artifacts; use --thread-id"}, indent=2))
        return 1
    checkpointer = _get_checkpointer()
    if checkpointer is None:
        print(
            json.dumps(
                {
                    "error": "Artifacts require a checkpointer (set CHECKPOINTER=postgres and DATABASE_URL, or use MemorySaver)",
                },
                indent=2,
            )
        )
        return 1
    try:
        from obligation_runtime_orchestrator.runtime.graph import build_patch_admissibility_graph
    except ImportError:
        print(json.dumps({"error": "langgraph not installed", "status": "failed"}, indent=2))
        return 1
    client = _client()
    graph = build_patch_admissibility_graph(client=client, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}
    try:
        snapshot = graph.get_state(config)
    except Exception as e:
        print(json.dumps({"error": f"Failed to get state: {e}", "thread_id": thread_id}, indent=2))
        return 1
    values = getattr(snapshot, "values", None) if snapshot else {}
    if not isinstance(values, dict):
        values = {}
    raw_artifacts = values.get("artifacts")
    artifacts: list[Any] = raw_artifacts if isinstance(raw_artifacts, list) else []
    if not values:
        print(
            json.dumps(
                {"message": "No checkpoint state for thread", "thread_id": thread_id}, indent=2
            )
        )
        return 0
    out = json.dumps(artifacts, indent=2)
    output_path = getattr(args, "output", None)
    if output_path:
        PathLib(output_path).write_text(out, encoding="utf-8")
        print(
            json.dumps(
                {
                    "thread_id": thread_id,
                    "artifacts_count": len(artifacts),
                    "written_to": output_path,
                },
                indent=2,
            )
        )
    else:
        print(out)
    return 0


def cmd_regressions(args: argparse.Namespace) -> int:
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    tests_dir = str(repo_root / "tests" / "regressions")
    code = subprocess.run(
        [sys.executable, "-m", "pytest", tests_dir, "-v", "--tb=short"], cwd=repo_root
    ).returncode
    return code


def main() -> int:
    parser = argparse.ArgumentParser(prog="obr")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_open = sub.add_parser("open-environment")
    p_open.add_argument("--repo-id", default="default")
    p_open.add_argument("--repo-path")
    p_open.add_argument("--repo-url")
    p_open.add_argument("--commit-sha", default="HEAD")
    p_open.set_defaults(func=cmd_open_environment)

    p_session = sub.add_parser("create-session")
    p_session.add_argument("fingerprint_id")
    p_session.set_defaults(func=cmd_create_session)

    p_patch = sub.add_parser("run-patch-obligation")
    p_patch.add_argument("--thread-id")
    p_patch.add_argument("--obligation-id")
    p_patch.add_argument("--repo-id")
    p_patch.add_argument("--repo-path")
    p_patch.add_argument("--target-files", nargs="*")
    p_patch.add_argument("--target-declarations", nargs="*", default=[])
    p_patch.add_argument("--patch-file")
    p_patch.add_argument(
        "--patch-apply-path",
        help="Workspace path to apply patch (default: basename of --patch-file)",
    )
    p_patch.add_argument(
        "--policy-pack", help="Policy pack name (e.g. reviewer_gated_execution_v1)"
    )
    p_patch.add_argument(
        "--protected-paths",
        nargs="*",
        default=None,
        help="Paths that require review when touched (e.g. Mini/Basic.lean)",
    )
    p_patch.add_argument(
        "--protocol-events-file", help="JSON file of protocol events (runtime-produced or offline)"
    )
    p_patch.set_defaults(func=cmd_run_patch_obligation)

    p_protocol = sub.add_parser("run-protocol-obligation")
    p_protocol.add_argument("--obligation-class", default="handoff_legality")
    p_protocol.add_argument("--pack", default="single_owner_handoff_v1")
    p_protocol.add_argument("--events-file")
    p_protocol.set_defaults(func=cmd_run_protocol_obligation)

    p_review = sub.add_parser("review")
    p_review.add_argument("thread_id", nargs="?")
    p_review.add_argument("--open-browser", action="store_true")
    p_review.set_defaults(func=cmd_review)

    p_resume = sub.add_parser("resume")
    p_resume.add_argument("thread_id", nargs="?")
    p_resume.add_argument("--decision", default="approved", help="approved or rejected")
    p_resume.set_defaults(func=cmd_resume)

    p_artifacts = sub.add_parser("artifacts")
    p_artifacts.add_argument("--thread-id", help="Thread ID to export artifacts for")
    p_artifacts.add_argument("--output", "-o", help="Write artifacts JSON to file")
    p_artifacts.set_defaults(func=cmd_artifacts)

    p_reg = sub.add_parser("regressions")
    p_reg.set_defaults(func=cmd_regressions)

    args = parser.parse_args()
    if args.cmd == "review" and not getattr(args, "thread_id", None):
        args.thread_id = ""
    if args.cmd == "resume" and not getattr(args, "thread_id", None):
        args.thread_id = ""
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
