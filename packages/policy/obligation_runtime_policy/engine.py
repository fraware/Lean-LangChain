from __future__ import annotations

import fnmatch
import os
from typing import Any, Literal

from obligation_runtime_schemas.policy import PolicyDecision, PolicyResolvedRule

from .models import PolicyPack

RuleEffect = Literal["none", "needs_review", "rejected", "blocked", "accepted"]


class PolicyEngine:
    """Pure, deterministic policy evaluation over normalized evidence."""

    def _rule(
        self,
        pack: PolicyPack,
        rule_id: str,
        matched: bool,
        effect: RuleEffect,
        reason_code: str,
    ) -> PolicyResolvedRule:
        return PolicyResolvedRule(
            rule_id=rule_id,
            source_pack=pack.name,
            matched=matched,
            effect=effect,
            reason_code=reason_code,
        )

    def evaluate(
        self,
        *,
        obligation: dict[str, Any],
        interactive_result: dict[str, Any] | None,
        batch_result: dict[str, Any] | None,
        patch_metadata: dict[str, Any],
        policy_pack: PolicyPack,
    ) -> PolicyDecision:
        pack = policy_pack
        rules: list[PolicyResolvedRule] = []
        reasons: list[str] = []

        changed_files = patch_metadata.get("changed_files") or []
        normalized: list[str] = []
        if isinstance(changed_files, list):
            normalized = [
                str(f).replace("\\", "/")
                for f in changed_files
                if isinstance(f, str) or isinstance(f, os.PathLike)
            ]

        if interactive_result and interactive_result.get("diagnostics"):
            error_like = [
                d for d in interactive_result["diagnostics"] if d.get("severity") == "error"
            ]
            if error_like:
                reasons.append("interactive_errors_present")
                rules.append(
                    self._rule(
                        pack, "interactive_errors", True, "rejected", "interactive_errors_present"
                    )
                )
                return PolicyDecision(
                    decision="rejected",
                    trust_level="blocked",
                    reasons=reasons,
                    policy_pack_name=pack.name,
                    policy_pack_version=pack.version,
                    resolved_rules=rules,
                )

        if batch_result:
            trust_level = batch_result.get("trust_level", "clean")
            if not batch_result.get("ok", False):
                reasons.append("batch_verify_failed")
                if batch_result.get("build", {}).get("ok") is False:
                    reasons.append("lake_build_failed")
                if batch_result.get("fresh_checker", {}).get("ok") is False:
                    reasons.append("fresh_checker_failed")
                rules.append(
                    self._rule(pack, "batch_verify", True, "rejected", "batch_verify_failed")
                )
                return PolicyDecision(
                    decision="rejected",
                    trust_level="blocked",
                    reasons=reasons,
                    policy_pack_name=pack.name,
                    policy_pack_version=pack.version,
                    resolved_rules=rules,
                )

            blocked_reasons = batch_result.get("axiom_audit", {}).get("blocked_reasons", [])
            if blocked_reasons:
                reasons.extend(blocked_reasons)
                rules.append(self._rule(pack, "axiom_audit", True, "blocked", "axiom_blocked"))
                return PolicyDecision(
                    decision="blocked",
                    trust_level="blocked",
                    reasons=reasons,
                    policy_pack_name=pack.name,
                    policy_pack_version=pack.version,
                    resolved_rules=rules,
                )

            if trust_level == "warning" and not pack.allow_trust_compiler:
                reasons.append("trust_compiler_detected")
                rules.append(
                    self._rule(
                        pack, "trust_compiler", True, "needs_review", "trust_compiler_detected"
                    )
                )
                return PolicyDecision(
                    decision="needs_review",
                    trust_level="warning",
                    reasons=reasons,
                    policy_pack_name=pack.name,
                    policy_pack_version=pack.version,
                    resolved_rules=rules,
                )

            for tg in pack.trust_gates:
                if trust_level not in tg.when_trust_level:
                    continue
                path_match = False
                if not tg.path_globs:
                    path_match = bool(normalized)
                else:
                    for f in normalized:
                        for g in tg.path_globs:
                            gg = g.replace("\\", "/")
                            if fnmatch.fnmatch(f, gg) or fnmatch.fnmatch(os.path.basename(f), gg):
                                path_match = True
                                break
                        if path_match:
                            break
                if path_match and tg.require_human:
                    reasons.append(tg.reason_code)
                    rules.append(
                        self._rule(
                            pack,
                            tg.rule_id,
                            True,
                            "needs_review",
                            tg.reason_code,
                        )
                    )
                    return PolicyDecision(
                        decision="needs_review",
                        trust_level="clean",
                        reasons=reasons,
                        policy_pack_name=pack.name,
                        policy_pack_version=pack.version,
                        resolved_rules=rules,
                    )

        if patch_metadata.get("trust_delta") and pack.require_human_on_trust_delta:
            reasons.append("trust_delta_requires_review")
            rules.append(
                self._rule(pack, "trust_delta", True, "needs_review", "trust_delta_requires_review")
            )
            return PolicyDecision(
                decision="needs_review",
                trust_level="clean",
                reasons=reasons,
                policy_pack_name=pack.name,
                policy_pack_version=pack.version,
                resolved_rules=rules,
            )

        for rule in pack.path_rules:
            g = rule.glob.replace("\\", "/")
            for f in normalized:
                if fnmatch.fnmatch(f, g) or fnmatch.fnmatch(os.path.basename(f), g):
                    if rule.require_human:
                        reasons.append(rule.reason_code)
                        rules.append(
                            self._rule(
                                pack,
                                f"path_rule:{rule.glob}",
                                True,
                                "needs_review",
                                rule.reason_code,
                            )
                        )
                        return PolicyDecision(
                            decision="needs_review",
                            trust_level="clean",
                            reasons=reasons,
                            policy_pack_name=pack.name,
                            policy_pack_version=pack.version,
                            resolved_rules=rules,
                        )
                    break

        if patch_metadata.get("protected_paths_touched"):
            reasons.append("protected_path_touched")
            rules.append(
                self._rule(pack, "protected_paths", True, "needs_review", "protected_path_touched")
            )
            return PolicyDecision(
                decision="needs_review",
                trust_level="clean",
                reasons=reasons,
                policy_pack_name=pack.name,
                policy_pack_version=pack.version,
                resolved_rules=rules,
            )

        if patch_metadata.get("imports_changed") and pack.require_human_if_imports_change:
            reasons.append("imports_changed_requires_review")
            rules.append(
                self._rule(
                    pack, "imports_changed", True, "needs_review", "imports_changed_requires_review"
                )
            )
            return PolicyDecision(
                decision="needs_review",
                trust_level="clean",
                reasons=reasons,
                policy_pack_name=pack.name,
                policy_pack_version=pack.version,
                resolved_rules=rules,
            )

        rules.append(self._rule(pack, "accept", True, "accepted", "accepted"))
        return PolicyDecision(
            decision="accepted",
            trust_level="clean",
            reasons=reasons,
            policy_pack_name=pack.name,
            policy_pack_version=pack.version,
            resolved_rules=rules,
        )
