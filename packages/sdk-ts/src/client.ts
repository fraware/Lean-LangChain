export type JsonObject = Record<string, unknown>;

export class ObligationRuntimeClient {
  constructor(private readonly baseUrl: string = "http://localhost:8000") {}

  private async post(path: string, payload: JsonObject): Promise<JsonObject> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return await res.json();
  }

  private async get(path: string): Promise<JsonObject> {
    const res = await fetch(`${this.baseUrl}${path}`);
    return await res.json();
  }

  openEnvironment(payload: JsonObject) { return this.post("/v1/environments/open", payload); }
  createSession(payload: JsonObject) { return this.post("/v1/sessions", payload); }
  applyPatch(sessionId: string, payload: JsonObject) { return this.post(`/v1/sessions/${sessionId}/apply-patch`, payload); }
  interactiveCheck(sessionId: string, payload: JsonObject) { return this.post(`/v1/sessions/${sessionId}/interactive-check`, payload); }
  getGoal(sessionId: string, payload: JsonObject) { return this.post(`/v1/sessions/${sessionId}/goal`, payload); }
  batchVerify(sessionId: string, payload: JsonObject) { return this.post(`/v1/sessions/${sessionId}/batch-verify`, payload); }
  getReviewPayload(threadId: string) { return this.get(`/v1/reviews/${threadId}`); }
  submitReviewDecision(threadId: string, decision: "approve" | "reject", payload: JsonObject) { return this.post(`/v1/reviews/${threadId}/${decision}`, payload); }
}
