from __future__ import annotations

from obligation_runtime_schemas.policy import PolicyDecision

from .models import PolicyPack


class PolicyEngine:
    """Pure, deterministic policy evaluation over normalized evidence."""

    def evaluate(
        self,
        *,
        obligation: dict,
        interactive_result: dict | None,
        batch_result: dict | None,
        patch_metadata: dict,
        policy_pack: PolicyPack,
    ) -> PolicyDecision:
        reasons: list[str] = []

        if interactive_result and interactive_result.get("diagnostics"):
            error_like = [d for d in interactive_result["diagnostics"] if d.get("severity") == "error"]
            if error_like:
                reasons.append("interactive_errors_present")
                return PolicyDecision(decision="rejected", trust_level="blocked", reasons=reasons)

        if batch_result:
            trust_level = batch_result.get("trust_level", "clean")
            if not batch_result.get("ok", False):
                reasons.append("batch_verify_failed")
                if batch_result.get("build", {}).get("ok") is False:
                    reasons.append("lake_build_failed")
                if batch_result.get("fresh_checker", {}).get("ok") is False:
                    reasons.append("fresh_checker_failed")
                return PolicyDecision(decision="rejected", trust_level="blocked", reasons=reasons)

            blocked_reasons = batch_result.get("axiom_audit", {}).get("blocked_reasons", [])
            if blocked_reasons:
                reasons.extend(blocked_reasons)
                return PolicyDecision(decision="blocked", trust_level="blocked", reasons=reasons)

            if trust_level == "warning" and not policy_pack.allow_trust_compiler:
                reasons.append("trust_compiler_detected")
                return PolicyDecision(decision="needs_review", trust_level="warning", reasons=reasons)

        if patch_metadata.get("protected_paths_touched"):
            reasons.append("protected_path_touched")
            return PolicyDecision(decision="needs_review", trust_level="clean", reasons=reasons)

        if patch_metadata.get("imports_changed") and policy_pack.require_human_if_imports_change:
            reasons.append("imports_changed_requires_review")
            return PolicyDecision(decision="needs_review", trust_level="clean", reasons=reasons)

        return PolicyDecision(decision="accepted", trust_level="clean", reasons=reasons)
