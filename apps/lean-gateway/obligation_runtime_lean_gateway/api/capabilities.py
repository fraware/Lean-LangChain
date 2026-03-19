"""Runtime capability snapshot: which Lean, audit, and store backends are active.

Used by /health, /ready, and startup logs so operators see degraded vs full verification.
"""

from __future__ import annotations

import os
from typing import Any, Literal

from obligation_runtime_schemas.degraded_reasons import ALL_DEGRADED_REASON_CODES

LeanInteractiveMode = Literal["real_lsp", "real_subprocess", "test_injected", "unconfigured"]
BackendMode = Literal["real", "test_injected", "unconfigured"]
ReviewStoreMode = Literal["postgres", "memory"]


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def compute_capability_snapshot() -> dict[str, Any]:
    """Current gateway capabilities (env + test injection). Safe to call from request handlers."""
    from obligation_runtime_lean_gateway.api import deps as d

    if d._test_transport is not None:  # noqa: SLF001
        lean: LeanInteractiveMode = "test_injected"
    elif _env_truthy("OBR_USE_LEAN_LSP"):
        lean = "real_lsp"
    elif _env_truthy("OBR_USE_REAL_LEAN"):
        lean = "real_subprocess"
    else:
        lean = "unconfigured"

    if d._test_axiom_auditor is not None:  # noqa: SLF001
        axiom: BackendMode = "test_injected"
    elif _env_truthy("OBR_USE_REAL_AXIOM_AUDIT"):
        axiom = "real"
    else:
        axiom = "unconfigured"

    if d._test_fresh_checker is not None:  # noqa: SLF001
        fresh: BackendMode = "test_injected"
    elif _env_truthy("OBR_USE_REAL_FRESH_CHECKER"):
        fresh = "real"
    else:
        fresh = "unconfigured"

    review_store: ReviewStoreMode = (
        "postgres"
        if os.environ.get("REVIEW_STORE", "memory") == "postgres"
        and (
            os.environ.get("REVIEW_STORE_POSTGRES_URI")
            or os.environ.get("DATABASE_URL", "").strip()
        )
        else "memory"
    )

    obr_env = (os.environ.get("OBR_ENV") or "").strip().lower()
    production = obr_env == "production"

    degraded_reasons: list[str] = []
    if not production:
        if lean == "unconfigured":
            degraded_reasons.append("lean_interactive_unconfigured")
        if axiom == "unconfigured":
            degraded_reasons.append("axiom_audit_unconfigured")
        if fresh == "unconfigured":
            degraded_reasons.append("fresh_checker_unconfigured")
        if review_store == "memory":
            degraded_reasons.append("review_store_memory")

    degraded = bool(degraded_reasons) and not production
    known = set(ALL_DEGRADED_REASON_CODES)
    degraded_reasons = [r for r in degraded_reasons if r in known]

    return {
        "lean_interactive": lean,
        "axiom_audit": axiom,
        "fresh_checker": fresh,
        "review_store": review_store,
        "degraded": degraded,
        "degraded_reasons": degraded_reasons,
        "obr_env": obr_env or "development",
    }


def log_capabilities_at_startup(logger: Any, *, app_version: str) -> None:
    """Emit gateway_capabilities log; WARN when degraded (dev) or lean missing (production)."""
    snap = compute_capability_snapshot()
    caps = {
        "lean_interactive": snap["lean_interactive"],
        "axiom_audit": snap["axiom_audit"],
        "fresh_checker": snap["fresh_checker"],
        "review_store": snap["review_store"],
    }
    msg = (
        f"event=gateway_capabilities version={app_version} "
        f"degraded={snap['degraded']} caps={caps!r} reasons={snap['degraded_reasons']!r}"
    )
    if snap["degraded"]:
        logger.warning("%s", msg)
    else:
        logger.info("%s", msg)
    if snap["obr_env"] == "production" and snap["lean_interactive"] == "unconfigured":
        logger.warning(
            "event=gateway_capabilities production lean_interactive=unconfigured "
            "(set OBR_USE_LEAN_LSP or OBR_USE_REAL_LEAN for full LSP/diagnostics)"
        )
