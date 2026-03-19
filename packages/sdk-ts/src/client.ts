import {
  ObligationRuntimeError,
  isApiError,
  type OpenEnvironmentPayload,
  type OpenEnvironmentResponse,
  type CreateSessionPayload,
  type CreateSessionResponse,
  type ApplyPatchPayload,
  type ApplyPatchResponse,
  type InteractiveCheckPayload,
  type InteractiveCheckResponse,
  type GetGoalPayload,
  type GetGoalResponse,
  type HoverPayload,
  type HoverResponse,
  type DefinitionPayload,
  type DefinitionResponse,
  type BatchVerifyPayload,
  type BatchVerifyResponse,
  type ReviewPayload,
  type CreatePendingReviewPayload,
  type CreatePendingReviewResponse,
  type SubmitReviewResponse,
  type ResumeResponse,
} from "./types";
import {
  assertBatchVerifyResponse,
  assertReviewPayload,
  assertResumeResponse,
} from "./validators";

export type ObligationRuntimeClientOptions = {
  /** When true, validates critical response bodies at runtime (small overhead). */
  validateResponses?: boolean;
};

async function parseErrorBody(
  res: Response
): Promise<{ code: string; message: string; request_id?: string; details?: Record<string, unknown> }> {
  let body: unknown;
  try {
    body = await res.json();
  } catch {
    return { code: "internal_error", message: res.statusText || "Unknown error" };
  }
  if (isApiError(body)) {
    const e = body.error;
    return {
      code: e.code,
      message: e.message,
      request_id: e.request_id,
      details: e.details,
    };
  }
  return { code: "internal_error", message: String(body) };
}

export class ObligationRuntimeClient {
  private readonly validateResponses: boolean;

  constructor(
    private readonly baseUrl: string = "http://localhost:8000",
    options?: ObligationRuntimeClientOptions
  ) {
    this.validateResponses = options?.validateResponses ?? false;
  }

  private parseSuccess<T>(path: string, data: unknown): T {
    if (!this.validateResponses) {
      return data as T;
    }
    try {
      if (path.includes("/batch-verify")) {
        assertBatchVerifyResponse(data);
      } else if (path.startsWith("/v1/reviews/") && !path.includes("/approve") && !path.includes("/reject") && !path.includes("/resume")) {
        assertReviewPayload(data);
      } else if (path.endsWith("/resume")) {
        assertResumeResponse(data);
      }
    } catch (e) {
      throw new ObligationRuntimeError(
        "response_validation_failed",
        e instanceof Error ? e.message : String(e),
        200
      );
    }
    return data as T;
  }

  private async post<T>(path: string, payload: object): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const { code, message, request_id, details } = await parseErrorBody(res);
      throw new ObligationRuntimeError(code, message, res.status, request_id, details);
    }
    const data: unknown = await res.json();
    return this.parseSuccess<T>(path, data);
  }

  private async get<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`);
    if (!res.ok) {
      const { code, message, request_id, details } = await parseErrorBody(res);
      throw new ObligationRuntimeError(code, message, res.status, request_id, details);
    }
    const data: unknown = await res.json();
    return this.parseSuccess<T>(path, data);
  }

  openEnvironment(payload: OpenEnvironmentPayload): Promise<OpenEnvironmentResponse> {
    return this.post("/v1/environments/open", payload);
  }

  createSession(payload: CreateSessionPayload): Promise<CreateSessionResponse> {
    return this.post("/v1/sessions", payload);
  }

  applyPatch(sessionId: string, payload: ApplyPatchPayload): Promise<ApplyPatchResponse> {
    return this.post(`/v1/sessions/${sessionId}/apply-patch`, payload);
  }

  interactiveCheck(sessionId: string, payload: InteractiveCheckPayload): Promise<InteractiveCheckResponse> {
    return this.post(`/v1/sessions/${sessionId}/interactive-check`, payload);
  }

  getGoal(sessionId: string, payload: GetGoalPayload): Promise<GetGoalResponse> {
    return this.post(`/v1/sessions/${sessionId}/goal`, payload);
  }

  hover(sessionId: string, payload: HoverPayload): Promise<HoverResponse> {
    return this.post(`/v1/sessions/${sessionId}/hover`, payload);
  }

  definition(sessionId: string, payload: DefinitionPayload): Promise<DefinitionResponse> {
    return this.post(`/v1/sessions/${sessionId}/definition`, payload);
  }

  batchVerify(sessionId: string, payload: BatchVerifyPayload): Promise<BatchVerifyResponse> {
    return this.post(`/v1/sessions/${sessionId}/batch-verify`, payload);
  }

  getReviewPayload(threadId: string): Promise<ReviewPayload> {
    return this.get(`/v1/reviews/${threadId}`);
  }

  createPendingReview(payload: CreatePendingReviewPayload): Promise<CreatePendingReviewResponse> {
    return this.post("/v1/reviews", payload);
  }

  submitReviewDecision(
    threadId: string,
    decision: "approve" | "reject",
    payload?: Record<string, unknown>
  ): Promise<SubmitReviewResponse> {
    return this.post(`/v1/reviews/${threadId}/${decision}`, payload ?? {});
  }

  resume(threadId: string): Promise<ResumeResponse> {
    return this.post(`/v1/reviews/${threadId}/resume`, {});
  }
}
