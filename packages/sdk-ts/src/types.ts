/**
 * Gateway API types derived from OpenAPI (`src/generated/gateway-openapi.ts`).
 * Regenerate with: npm run generate:types
 */

import type { components } from "./generated/gateway-openapi";

type Schemas = components["schemas"];

export type TrustLevel = Schemas["BatchVerifyResult"]["trust_level"];

export type OpenEnvironmentPayload = Schemas["OpenEnvironmentRequest"];
export type OpenEnvironmentResponse = Schemas["OpenEnvironmentResponse"];
export type CreateSessionPayload = Schemas["CreateSessionRequest"];
export type CreateSessionResponse = Schemas["CreateSessionResponse"];
export type ApplyPatchPayload = Schemas["ApplyPatchRequest"];
export type ApplyPatchResponse = Schemas["ApplyPatchResponse"];
export type InteractiveCheckPayload = Schemas["InteractiveCheckRequest"];
export type InteractiveCheckResponse = Schemas["InteractiveCheckApiResponse"];
export type GetGoalPayload = Schemas["SessionGoalRequest"];
export type GetGoalResponse = Schemas["SessionGoalResponse"];
export type HoverPayload = Schemas["SessionHoverRequest"];
export type HoverResponse = Schemas["SessionHoverResponse"];
export type DefinitionPayload = Schemas["SessionDefinitionRequest"];
export type DefinitionResponse = Schemas["SessionDefinitionResponse"];
export type BatchVerifyPayload = Schemas["BatchVerifyRequest"];
export type BatchVerifyResponse = Schemas["BatchVerifyResult"];
export type BatchBuildResult = Schemas["BatchBuildResult"];
export type AxiomDependency = Schemas["AxiomDependency"];
export type AxiomAuditResult = Schemas["AxiomAuditResult"];
export type FreshCheckerResult = Schemas["FreshCheckerResult"];
export type ReviewPayload = Schemas["ReviewPayload"];
export type CreatePendingReviewPayload = Schemas["CreatePendingReviewRequest"];
export type CreatePendingReviewResponse = Schemas["CreatePendingReviewResponse"];
export type SubmitReviewResponse = Schemas["ReviewDecisionResponse"];
export type ResumeResponse = Schemas["ReviewResumeProxyResponse"];
export type GatewayHealthResponse = Schemas["GatewayHealthResponse"];

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

export type { components as GatewayOpenAPIComponents } from "./generated/gateway-openapi";
