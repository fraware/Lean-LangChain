"""LangGraph patch-admissibility flow. V1: single obligation, terminal state emits WitnessBundle.

Node implementations live inline in this module (build_patch_admissibility_graph). The runtime/nodes/
directory is unused; graph logic is kept here for a single source of truth.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable

from langgraph.graph import END, START, StateGraph

from obligation_runtime_orchestrator.runtime.state import ObligationRuntimeState
from obligation_runtime_schemas.common import new_id

logger = logging.getLogger(__name__)

SPAN_BY_NODE: dict[str, str] = {
    "init_environment": "obr.init_environment",
    "retrieve_context": "obr.retrieve_context",
    "draft_candidate": "obr.retrieve_context",
    "interactive_check": "obr.interactive_check",
    "batch_verify": "obr.batch_verify",
    "audit_trust": "obr.audit_trust",
    "policy_review": "obr.policy_review",
    "interrupt_for_approval": "obr.interrupt_for_approval",
    "finalize": "obr.finalize",
    "resume_with_approval": "obr.finalize",
    "repair_from_diagnostics": "obr.interactive_check",
    "repair_from_goals": "obr.interactive_check",
}


def _route_after_interactive(state: ObligationRuntimeState) -> str:
    ir = state.get("interactive_result")
    if not ir:
        return "batch_verify"
    if not ir.get("ok"):
        return "repair_from_diagnostics"
    if ir.get("goals") and any(g.get("text") for g in ir.get("goals", [])):
        return "repair_from_goals"
    return "batch_verify"


def _route_after_policy(state: ObligationRuntimeState) -> str:
    pd = state.get("policy_decision")
    if not pd:
        return "finalize"
    decision = pd.get("decision", "failed")
    if decision == "accepted":
        return "finalize"
    if decision == "needs_review":
        return "interrupt_for_approval"
    return "__end__"


def _route_start(state: ObligationRuntimeState) -> str:
    """Resume path: if approval_decision is set, go to resume node; else start fresh."""
    if state.get("approval_required") and state.get("approval_decision") in ("approved", "rejected"):
        return "resume_with_approval"
    return "init_environment"


def _route_after_resume(state: ObligationRuntimeState) -> str:
    """After resume: approved -> finalize, rejected -> end."""
    if state.get("approval_decision") == "approved":
        return "finalize"
    return "__end__"


def _emit(
    tracer: Any,
    state: ObligationRuntimeState,
    node_name: str,
    event_type: str,
    status: str,
    timing_ms: int | None = None,
    failure_class: str | None = None,
) -> None:
    if tracer is None or not hasattr(tracer, "emit"):
        return
    span_name = SPAN_BY_NODE.get(node_name, f"obr.{node_name}")
    env = state.get("environment_fingerprint") or {}
    env_hash = env.get("fingerprint_id") or str(hash(str(env)))[:16]
    event: dict[str, Any] = {
        "event_type": event_type,
        "span_name": span_name,
        "thread_id": state.get("thread_id") or "",
        "obligation_id": state.get("obligation_id") or "",
        "node_name": node_name,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timing_ms": timing_ms,
        "failure_class": failure_class,
        "metadata": {
            "session_id": state.get("session_id"),
            "environment_fingerprint_hash": env_hash,
        },
    }
    tracer.emit(event)


def _with_tracing(
    tracer: Any,
    node_name: str,
    fn: Callable[[ObligationRuntimeState], dict],
) -> Callable[[ObligationRuntimeState], dict]:
    def wrapped(state: ObligationRuntimeState) -> dict:
        _emit(tracer, state, node_name, "node_enter", state.get("status") or "running")
        start = time.monotonic()
        try:
            out = fn(state)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            _emit(
                tracer,
                {**state, **out},
                node_name,
                "node_exit",
                out.get("status") or "ok",
                timing_ms=elapsed_ms,
            )
            return out
        except Exception as e:
            _emit(
                tracer,
                state,
                node_name,
                "node_error",
                "failed",
                failure_class=type(e).__name__,
            )
            raise

    return wrapped


def build_patch_admissibility_graph(
    gateway_base_url: str = "http://localhost:8000",
    client: Any = None,
    tracer: Any = None,
    checkpointer: Any = None,
) -> Any:
    from obligation_runtime_sdk.client import ObligationRuntimeClient
    from obligation_runtime_policy.constants import (
        DECISION_BLOCKED,
        REASON_MISSING_APPROVAL_TOKEN,
        TRUST_BLOCKED,
    )
    from obligation_runtime_policy.engine import PolicyEngine
    from obligation_runtime_policy.models import PolicyPack
    from obligation_runtime_policy.pack_loader import load_pack
    from obligation_runtime_policy.patch_metadata import summarize_patch
    from obligation_runtime_policy.protocol_evaluator import evaluate_protocol_obligation

    if client is None:
        client = ObligationRuntimeClient(base_url=gateway_base_url)
    policy_engine = PolicyEngine()

    _DEFAULT_PACK = PolicyPack(version="1", name="strict", description="Strict")
    _DEFAULT_PACK_NAME = "strict_patch_gate_v1"

    def _load_pack_for_review(state: ObligationRuntimeState) -> PolicyPack:
        name = (
            state.get("policy_pack_name")
            or os.environ.get("OBR_POLICY_PACK", _DEFAULT_PACK_NAME)
        )
        try:
            return load_pack(name)
        except (FileNotFoundError, OSError) as e:
            logger.warning("Policy pack %r not loadable: %s; using default", name, e)
            return _DEFAULT_PACK
        except Exception as e:  # ValidationError, etc.
            logger.warning(
                "Policy pack %r validation failed: %s; using default", name, e
            )
            return _DEFAULT_PACK

    def init_environment(state: ObligationRuntimeState) -> dict:
        ob = state.get("obligation", {})
        env = ob.get("environment_fingerprint", {}) or state.get("environment_fingerprint", {})
        repo_id = (ob.get("target") or {}).get("repo_id") or env.get("repo_id") or "default"
        repo_path = state.get("_repo_path") or ""
        open_data = client.open_environment(repo_id=repo_id, repo_path=repo_path or None, commit_sha="HEAD")
        fid = open_data["fingerprint_id"]
        session_data = client.create_session(fingerprint_id=fid)
        return {
            "session_id": session_data["session_id"],
            "environment_fingerprint": open_data.get("fingerprint", env),
            "status": "initialized",
        }

    def retrieve_context(state: ObligationRuntimeState) -> dict:
        return {"status": "retrieving_context"}

    def draft_candidate(state: ObligationRuntimeState) -> dict:
        return {"status": "drafting"}

    def interactive_check(state: ObligationRuntimeState) -> dict:
        sid = state.get("session_id")
        if not sid:
            return {"status": "failed"}
        current_patch = state.get("current_patch") or {}
        if current_patch:
            client.apply_patch(session_id=sid, files=current_patch)
        target_files = state.get("target_files") or []
        file_path = target_files[0] if target_files else "Main.lean"
        result = client.interactive_check(session_id=sid, file_path=file_path)
        return {"interactive_result": result, "status": "checking_interactive"}

    def batch_verify(state: ObligationRuntimeState) -> dict:
        sid = state.get("session_id")
        if not sid:
            return {"status": "failed"}
        target_declarations = state.get("target_declarations") or []
        target_files = state.get("target_files") or []
        result = client.batch_verify(
            session_id=sid,
            target_files=target_files,
            target_declarations=target_declarations,
        )
        return {"batch_result": result, "status": "batch_verifying", "trust_level": result.get("trust_level")}

    def audit_trust(state: ObligationRuntimeState) -> dict:
        return {"status": "auditing"}

    def evaluate_protocol(state: ObligationRuntimeState) -> dict:
        events = state.get("protocol_events") or []
        if not events:
            return {}
        pack_name = (
            state.get("policy_pack_name")
            or os.environ.get("OBR_POLICY_PACK", "single_owner_handoff_v1")
        )
        try:
            pack = load_pack(pack_name)
        except (FileNotFoundError, OSError) as e:
            logger.warning(
                "evaluate_protocol: pack %r not loadable: %s", pack_name, e
            )
            return {}
        except Exception as e:
            logger.warning("evaluate_protocol: pack %r failed: %s", pack_name, e)
            return {}
        for obligation_class, pack_attr in (
            ("handoff_legality", "single_owner_handoff"),
            ("lock_ownership_invariant", "lock_ownership_invariant"),
            ("delegation_admissibility", "delegation_admissibility"),
            ("state_transition_preservation", "state_transition_preservation"),
            ("artifact_admissibility", "artifact_admissibility"),
            ("side_effect_authorization", "side_effect_authorization"),
            ("evidence_complete_execution_token", "evidence_complete_execution_token"),
        ):
            if not getattr(pack, pack_attr, False):
                continue
            decision = evaluate_protocol_obligation(obligation_class, events, pack)
            if decision.decision in ("rejected", "blocked"):
                return {
                    "policy_decision": decision.model_dump(mode="json"),
                    "status": "auditing",
                }
        return {}

    def policy_review(state: ObligationRuntimeState) -> dict:
        existing = state.get("policy_decision") or {}
        if existing.get("decision") in ("rejected", "blocked"):
            return {"status": "auditing"}
        pack = _load_pack_for_review(state)
        if pack.reviewer_gated_execution:
            approval = state.get("approval_decision")
            if approval not in ("approved", "rejected"):
                return {
                    "policy_decision": {
                        "decision": DECISION_BLOCKED,
                        "trust_level": TRUST_BLOCKED,
                        "reasons": [REASON_MISSING_APPROVAL_TOKEN],
                    },
                    "status": "auditing",
                }
        ob = state.get("obligation") or {}
        policy = ob.get("policy") or {}
        protected_paths = list(policy.get("protected_paths") or [])
        after = state.get("current_patch") or {}
        summary = summarize_patch(before={}, after=after, protected_paths=protected_paths)
        patch_meta = {
            "protected_paths_touched": summary["protected_paths_touched"],
            "imports_changed": summary["imports_changed"],
        }
        decision = policy_engine.evaluate(
            obligation=state.get("obligation", {}),
            interactive_result=state.get("interactive_result"),
            batch_result=state.get("batch_result"),
            patch_metadata=patch_meta,
            policy_pack=pack,
        )
        return {
            "policy_decision": decision.model_dump(mode="json"),
            "status": "auditing",
        }

    def interrupt_for_approval(state: ObligationRuntimeState) -> dict:
        thread_id = state.get("thread_id") or ""
        obligation = state.get("obligation") or {}
        policy = obligation.get("policy") or {}
        protected_paths = list(policy.get("protected_paths") or [])
        after = state.get("current_patch") or {}
        summary = summarize_patch(before={}, after=after, protected_paths=protected_paths)
        review_payload = {
            "thread_id": thread_id,
            "obligation_id": state.get("obligation_id") or "",
            "obligation_summary": {"obligation": obligation, "target_files": state.get("target_files"), "target_declarations": state.get("target_declarations")},
            "environment_summary": state.get("environment_fingerprint") or {},
            "patch_metadata": {
                "current_patch": state.get("current_patch"),
                "protected_paths_touched": summary["protected_paths_touched"],
                "imports_changed": summary["imports_changed"],
                "changed_files": summary.get("changed_files", []),
                "diff_hash": summary.get("diff_hash"),
            },
            "diff_summary": None,
            "diagnostics_summary": (state.get("interactive_result") or {}).get("diagnostics", []),
            "axiom_audit_summary": (state.get("batch_result") or {}).get("axiom_audit", {}),
            "batch_summary": state.get("batch_result") or {},
            "policy_summary": state.get("policy_decision") or {},
            "trust_delta": state.get("trust_level"),
            "reasons": (state.get("policy_decision") or {}).get("reasons", []),
            "status": "awaiting_review",
        }
        try:
            client.create_pending_review(review_payload)
        except Exception:
            pass
        return {"approval_required": True, "status": "awaiting_approval"}

    def finalize(state: ObligationRuntimeState) -> dict:
        from obligation_runtime_schemas.environment import EnvironmentFingerprint
        from obligation_runtime_schemas.interactive import InteractiveCheckResult
        from obligation_runtime_schemas.policy import PolicyDecision
        from obligation_runtime_schemas.witness import WitnessBundle

        env = state.get("environment_fingerprint") or {}
        inter = state.get("interactive_result") or {}
        batch = state.get("batch_result") or {}
        policy = state.get("policy_decision") or {}
        try:
            env_fp = EnvironmentFingerprint.model_validate(env) if isinstance(env, dict) else env
        except Exception:
            env_fp = EnvironmentFingerprint(repo_id="", commit_sha="", lean_toolchain="", lakefile_hash="", **{k: v for k, v in (env or {}).items() if k in ["repo_id", "commit_sha", "lean_toolchain", "lakefile_hash"]})
        try:
            inter_result = InteractiveCheckResult.model_validate(inter) if isinstance(inter, dict) else inter
        except Exception:
            inter_result = InteractiveCheckResult(ok=True, diagnostics=[], goals=[])
        try:
            policy_dec = PolicyDecision.model_validate(policy) if isinstance(policy, dict) else policy
        except Exception:
            policy_dec = PolicyDecision(decision="accepted", trust_level="clean", reasons=[])
        approval_val = state.get("approval_decision")
        approval_dict: dict = approval_val if isinstance(approval_val, dict) else {}
        bundle = WitnessBundle(
            bundle_id=new_id("wit"),
            obligation_id=state.get("obligation_id", ""),
            environment_fingerprint=env_fp,
            interactive=inter_result,
            acceptance=batch,
            policy=policy_dec,
            approval=approval_dict,
            trace={},
        )
        artifacts = list(state.get("artifacts") or [])
        artifacts.append({"kind": "witness_bundle", "bundle": bundle.model_dump(mode="json")})
        return {"status": "accepted", "artifacts": artifacts}

    def repair_from_diagnostics(state: ObligationRuntimeState) -> dict:
        return {"status": "repairing"}

    def repair_from_goals(state: ObligationRuntimeState) -> dict:
        return {"status": "repairing"}

    def resume_with_approval(state: ObligationRuntimeState) -> dict:
        decision = state.get("approval_decision") or "rejected"
        return {"approval_required": False, "status": "accepted" if decision == "approved" else "rejected"}

    def wrap(name: str, f: Callable[[ObligationRuntimeState], dict]) -> Callable[[ObligationRuntimeState], dict]:
        return _with_tracing(tracer, name, f)

    builder = StateGraph(ObligationRuntimeState)
    builder.add_node("init_environment", wrap("init_environment", init_environment))  # type: ignore[call-overload]
    builder.add_node("resume_with_approval", wrap("resume_with_approval", resume_with_approval))  # type: ignore[call-overload]
    builder.add_node("retrieve_context", wrap("retrieve_context", retrieve_context))  # type: ignore[call-overload]
    builder.add_node("draft_candidate", wrap("draft_candidate", draft_candidate))  # type: ignore[call-overload]
    builder.add_node("interactive_check", wrap("interactive_check", interactive_check))  # type: ignore[call-overload]
    builder.add_node("batch_verify", wrap("batch_verify", batch_verify))  # type: ignore[call-overload]
    builder.add_node("audit_trust", wrap("audit_trust", audit_trust))  # type: ignore[call-overload]
    builder.add_node("evaluate_protocol", wrap("evaluate_protocol", evaluate_protocol))  # type: ignore[call-overload]
    builder.add_node("policy_review", wrap("policy_review", policy_review))  # type: ignore[call-overload]
    builder.add_node("interrupt_for_approval", wrap("interrupt_for_approval", interrupt_for_approval))  # type: ignore[call-overload]
    builder.add_node("finalize", wrap("finalize", finalize))  # type: ignore[call-overload]
    builder.add_node("repair_from_diagnostics", wrap("repair_from_diagnostics", repair_from_diagnostics))  # type: ignore[call-overload]
    builder.add_node("repair_from_goals", wrap("repair_from_goals", repair_from_goals))  # type: ignore[call-overload]

    builder.add_conditional_edges(
        START,
        _route_start,
        {"init_environment": "init_environment", "resume_with_approval": "resume_with_approval"},
    )
    builder.add_edge("init_environment", "retrieve_context")
    builder.add_edge("retrieve_context", "draft_candidate")
    builder.add_edge("draft_candidate", "interactive_check")
    builder.add_conditional_edges(
        "interactive_check",
        _route_after_interactive,
        {"batch_verify": "batch_verify", "repair_from_diagnostics": "repair_from_diagnostics", "repair_from_goals": "repair_from_goals"},
    )
    builder.add_edge("batch_verify", "audit_trust")
    builder.add_edge("audit_trust", "evaluate_protocol")
    builder.add_edge("evaluate_protocol", "policy_review")
    builder.add_conditional_edges(
        "policy_review",
        _route_after_policy,
        {"finalize": "finalize", "interrupt_for_approval": "interrupt_for_approval", "__end__": "__end__"},
    )
    builder.add_edge("finalize", END)
    builder.add_conditional_edges(
        "resume_with_approval",
        _route_after_resume,
        {"finalize": "finalize", "__end__": "__end__"},
    )
    builder.add_edge("interrupt_for_approval", END)
    builder.add_edge("repair_from_diagnostics", END)
    builder.add_edge("repair_from_goals", END)

    if checkpointer is not None:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()
