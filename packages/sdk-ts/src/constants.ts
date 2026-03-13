/**
 * Gateway / acceptance-lane constants and helpers for use with the TypeScript SDK.
 * Keep in sync with obligation_runtime_lean_gateway.batch.axiom_audit (NON_REAL_AXIOM_AUDIT_REASON).
 */

import type { BatchVerifyResponse } from "./types";

/** Reason code in batch-verify when axiom audit was not real (test double or unconfigured). */
export const AXIOM_AUDIT_NON_REAL_REASON = "axiom_audit_stub_unconfigured" as const;

/**
 * Returns true if the batch-verify response indicates axiom audit was not real (no real evidence).
 * Use when axiom_evidence_real is false or when reasons include AXIOM_AUDIT_NON_REAL_REASON.
 */
export function isNonRealAxiomAudit(response: BatchVerifyResponse): boolean {
  if (response.axiom_evidence_real === true) return false;
  const reasons = response.axiom_audit?.blocked_reasons ?? [];
  return reasons.includes(AXIOM_AUDIT_NON_REAL_REASON);
}

/** @deprecated Use AXIOM_AUDIT_NON_REAL_REASON. */
export const AXIOM_AUDIT_STUB_REASON = AXIOM_AUDIT_NON_REAL_REASON;

/** @deprecated Use isNonRealAxiomAudit. */
export function isStubAxiomAudit(response: BatchVerifyResponse): boolean {
  return isNonRealAxiomAudit(response);
}

/** Responses that may include lsp_required when LSP is not configured. */
export interface LspRequiredResponse {
  lsp_required?: boolean;
}

/**
 * Returns true if the response indicates LSP is required (goal/hover/definition/interactive-check
 * return empty data when LSP is not configured).
 */
export function isLspRequired(response: LspRequiredResponse): boolean {
  return response.lsp_required === true;
}
