import type { ReviewPayload } from "./models";

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8000";

export async function fetchReview(threadId: string): Promise<ReviewPayload | null> {
  const res = await fetch(`${GATEWAY_URL}/v1/reviews/${threadId}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as ReviewPayload;
}

export async function submitApproval(threadId: string): Promise<{ ok: boolean }> {
  const res = await fetch(`${GATEWAY_URL}/v1/reviews/${threadId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as { ok: boolean };
}

export async function submitReject(threadId: string): Promise<{ ok: boolean }> {
  const res = await fetch(`${GATEWAY_URL}/v1/reviews/${threadId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as { ok: boolean };
}

export type ResumeResult = {
  ok: boolean;
  thread_id: string;
  status?: string;
  artifacts_count?: number;
};

export async function submitResume(threadId: string): Promise<ResumeResult> {
  const res = await fetch(`${GATEWAY_URL}/v1/reviews/${threadId}/resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as ResumeResult;
}
