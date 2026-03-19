"""Orchestrator runtime capability snapshot for /health, /ready, and startup logs."""

from __future__ import annotations

import os
from typing import Any

from obligation_runtime_schemas.degraded_reasons import ALL_DEGRADED_REASON_CODES


def _policy_pack_resolves() -> bool:
    """Best-effort: OBR_POLICY_PACK (or default) loads successfully."""
    ref = (os.environ.get("OBR_POLICY_PACK") or "strict_patch_gate_v1").strip()
    try:
        from obligation_runtime_policy.pack_loader import load_pack

        load_pack(ref)
        return True
    except Exception:
        return False


def _checkpointer_kind() -> str:
    """Infer configured checkpointer without opening DB connections."""
    if os.environ.get("CHECKPOINTER") == "postgres" and os.environ.get("DATABASE_URL", "").strip():
        try:
            import langgraph.checkpoint.postgres  # noqa: F401

            return "postgres"
        except ImportError:
            return "unavailable"
    try:
        import langgraph.checkpoint.memory  # noqa: F401

        return "memory"
    except ImportError:
        return "unavailable"


def compute_orchestrator_capabilities() -> dict[str, Any]:
    checkpointer_kind = _checkpointer_kind()
    policy_ref = (os.environ.get("OBR_POLICY_PACK") or "strict_patch_gate_v1").strip()
    gateway_ok = bool((os.environ.get("OBR_GATEWAY_URL") or "http://localhost:8000").strip())

    langgraph_ok = True
    try:
        import langgraph  # noqa: F401
    except ImportError:
        langgraph_ok = False

    obr_env = (os.environ.get("OBR_ENV") or "").strip().lower()
    production = obr_env == "production"
    degraded_reasons: list[str] = []
    if not production:
        if checkpointer_kind == "memory":
            degraded_reasons.append("checkpointer_memory")
        if checkpointer_kind == "unavailable":
            degraded_reasons.append("checkpointer_unavailable")
        if not langgraph_ok:
            degraded_reasons.append("langgraph_unavailable")
        if not _policy_pack_resolves():
            degraded_reasons.append("policy_pack_unresolved")
    degraded = bool(degraded_reasons) and not production

    return {
        "checkpointer": checkpointer_kind,
        "policy_pack_ref": policy_ref,
        "gateway_url_configured": gateway_ok,
        "langgraph_runtime": langgraph_ok,
        "degraded": degraded,
        "degraded_reasons": degraded_reasons,
        "obr_env": obr_env or "development",
    }


def validate_reason_codes(reasons: list[str]) -> list[str]:
    known = set(ALL_DEGRADED_REASON_CODES)
    return [r for r in reasons if r in known]


def log_orchestrator_capabilities(logger: Any, *, app_version: str) -> None:
    snap = compute_orchestrator_capabilities()
    caps = {
        "checkpointer": snap["checkpointer"],
        "policy_pack_ref": snap["policy_pack_ref"],
        "gateway_url_configured": snap["gateway_url_configured"],
        "langgraph_runtime": snap["langgraph_runtime"],
    }
    msg = (
        f"event=orchestrator_capabilities version={app_version} "
        f"degraded={snap['degraded']} caps={caps!r} reasons={snap['degraded_reasons']!r}"
    )
    if snap["degraded"]:
        logger.warning("%s", msg)
    else:
        logger.info("%s", msg)
    if snap["obr_env"] == "production" and snap["checkpointer"] == "memory":
        logger.warning(
            "event=orchestrator_capabilities production checkpointer=memory "
            "(set CHECKPOINTER=postgres and DATABASE_URL for durable checkpoints)"
        )
