"""LangGraph patch-admissibility flow. V1: single obligation, terminal state emits WitnessBundle.

Graph assembly and tracing live here; node logic and routing are in runtime/nodes/handlers.py
and runtime/routes.py for composable boundaries.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable

from langgraph.graph import END, START, StateGraph

from obligation_runtime_orchestrator.runtime.state import ObligationRuntimeState

from .nodes.handlers import create_node_handlers
from .routes import (
    route_after_interactive,
    route_after_policy,
    route_after_resume,
    route_start,
)

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
    from obligation_runtime_policy.engine import PolicyEngine
    from obligation_runtime_policy.models import PolicyPack
    from obligation_runtime_policy.pack_loader import load_pack

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
        except Exception as e:
            logger.warning(
                "Policy pack %r validation failed: %s; using default", name, e
            )
            return _DEFAULT_PACK

    handlers = create_node_handlers(
        client=client,
        policy_engine=policy_engine,
        load_pack=load_pack,
        load_pack_for_review=_load_pack_for_review,
    )

    def wrap(name: str, f: Callable[[ObligationRuntimeState], dict]) -> Callable[[ObligationRuntimeState], dict]:
        return _with_tracing(tracer, name, f)

    builder = StateGraph(ObligationRuntimeState)
    for name, fn in handlers.items():
        builder.add_node(name, wrap(name, fn))  # type: ignore[call-overload]

    builder.add_conditional_edges(
        START,
        route_start,
        {"init_environment": "init_environment", "resume_with_approval": "resume_with_approval"},
    )
    builder.add_edge("init_environment", "retrieve_context")
    builder.add_edge("retrieve_context", "draft_candidate")
    builder.add_edge("draft_candidate", "interactive_check")
    builder.add_conditional_edges(
        "interactive_check",
        route_after_interactive,
        {"batch_verify": "batch_verify", "repair_from_diagnostics": "repair_from_diagnostics", "repair_from_goals": "repair_from_goals"},
    )
    builder.add_edge("batch_verify", "audit_trust")
    builder.add_edge("audit_trust", "evaluate_protocol")
    builder.add_edge("evaluate_protocol", "policy_review")
    builder.add_conditional_edges(
        "policy_review",
        route_after_policy,
        {"finalize": "finalize", "interrupt_for_approval": "interrupt_for_approval", "__end__": "__end__"},
    )
    builder.add_edge("finalize", END)
    builder.add_conditional_edges(
        "resume_with_approval",
        route_after_resume,
        {"finalize": "finalize", "__end__": "__end__"},
    )
    builder.add_edge("interrupt_for_approval", END)
    builder.add_edge("repair_from_diagnostics", END)
    builder.add_edge("repair_from_goals", END)

    if checkpointer is not None:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()
