/**
 * Gateway API request/response types and normalized error envelope.
 * Aligned with Lean Gateway routes and obligation_runtime_schemas.
 */

export type TrustLevel = "clean" | "warning" | "blocked";

/** Normalized error envelope returned by Gateway on 4xx/5xx. */
export interface ApiErrorBody {
  code: string;
  message: string;
  request_id?: string;
  details?: Record<string, unknown>;
}

export function isApiError(obj: unknown): obj is { error: ApiErrorBody } {
  return (
    typeof obj === "object" &&
    obj !== null &&
    "error" in obj &&
    typeof (obj as { error: unknown }).error === "object" &&
    (obj as { error: ApiErrorBody }).error !== null &&
    typeof (obj as { error: ApiErrorBody }).error.code === "string" &&
    typeof (obj as { error: ApiErrorBody }).error.message === "string"
  );
}

/** Thrown on failed HTTP responses; carries Gateway error envelope. */
export class ObligationRuntimeError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly statusCode: number,
    public readonly requestId?: string,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "ObligationRuntimeError";
    Object.setPrototypeOf(this, ObligationRuntimeError.prototype);
  }
}

// --- Environment ---
export interface OpenEnvironmentPayload {
  repo_id: string;
  repo_path?: string;
  repo_url?: string;
  commit_sha?: string;
}

export interface OpenEnvironmentResponse {
  fingerprint: Record<string, unknown>;
  fingerprint_id: string;
  snapshot_path: string;
}

// --- Sessions ---
export interface CreateSessionPayload {
  fingerprint_id: string;
}

export interface CreateSessionResponse {
  session_id: string;
  fingerprint_id: string;
  workspace_path: string;
}

export interface ApplyPatchPayload {
  files: Record<string, string>;
}

export interface ApplyPatchResponse {
  ok: boolean;
  session_id: string;
  changed_files: string[];
}

export interface InteractiveCheckPayload {
  file_path: string;
}

export interface InteractiveCheckResponse {
  ok: boolean;
  diagnostics?: unknown[];
  goals?: unknown[];
  /** True when LSP is not configured (full diagnostics/goals require OBR_USE_LEAN_LSP). */
  lsp_required?: boolean;
}

export interface GetGoalPayload {
  file_path: string;
  line: number;
  column: number;
  goal_kind?: string;
}

export interface GetGoalResponse {
  ok: boolean;
  goal_kind: string;
  goals: unknown;
  line: number;
  column: number;
  /** True when LSP is not configured (goal/hover/definition require OBR_USE_LEAN_LSP). */
  lsp_required?: boolean;
}

export interface HoverPayload {
  file_path: string;
  line: number;
  column: number;
}

export interface HoverResponse {
  ok: boolean;
  contents: unknown;
  file_path: string;
  line: number;
  column: number;
  lsp_required?: boolean;
}

export interface DefinitionPayload {
  file_path: string;
  line: number;
  column: number;
}

export interface DefinitionResponse {
  ok: boolean;
  locations: unknown;
  file_path: string;
  line: number;
  column: number;
  lsp_required?: boolean;
}

// --- Batch verify (acceptance lane) ---
export interface BatchBuildResult {
  ok: boolean;
  command: string[];
  stdout?: string;
  stderr?: string;
  timing_ms?: number;
}

export interface AxiomDependency {
  declaration: string;
  axioms: string[];
}

export interface AxiomAuditResult {
  ok: boolean;
  trust_level: TrustLevel;
  blocked_reasons?: string[];
  dependencies?: AxiomDependency[];
}

export interface FreshCheckerResult {
  ok: boolean;
  command?: string[];
  stdout?: string;
  stderr?: string;
  timing_ms?: number;
}

export interface BatchVerifyPayload {
  target_files?: string[];
  target_declarations?: string[];
}

export interface BatchVerifyResponse {
  ok: boolean;
  build: BatchBuildResult;
  axiom_audit: AxiomAuditResult;
  fresh_checker: FreshCheckerResult;
  trust_level: TrustLevel;
  reasons: string[];
  axiom_evidence_real?: boolean;
  fresh_evidence_real?: boolean;
}

// --- Review ---
export type ReviewPayload = Record<string, unknown>;

export interface CreatePendingReviewPayload {
  thread_id: string;
  [key: string]: unknown;
}

export interface CreatePendingReviewResponse {
  ok: boolean;
  thread_id: string;
}

export interface SubmitReviewResponse {
  ok: boolean;
  thread_id: string;
  decision: "approved" | "rejected";
}

export interface ResumeResponse {
  ok: boolean;
  thread_id: string;
  status?: string;
  artifacts_count?: number;
}
