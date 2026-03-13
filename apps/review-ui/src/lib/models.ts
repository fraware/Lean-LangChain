export type ReviewPayload = {
  thread_id: string;
  obligation_id: string;
  obligation_summary?: Record<string, unknown>;
  environment_summary?: Record<string, unknown>;
  patch_metadata?: Record<string, unknown>;
  diff_summary?: string | null;
  diagnostics_summary?: Record<string, unknown> | unknown[];
  axiom_audit_summary?: Record<string, unknown>;
  batch_summary?: Record<string, unknown>;
  policy_summary?: Record<string, unknown>;
  trust_delta?: string | null;
  reasons?: string[];
  status: "awaiting_review" | "approved" | "rejected";
};
