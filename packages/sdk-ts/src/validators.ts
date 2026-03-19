/**
 * Optional runtime validation for critical SDK responses (defense in depth).
 * Schemas mirror gateway OpenAPI; keep in sync when regenerating types.
 */

import { z } from "zod";

const trustLevel = z.enum(["clean", "warning", "blocked"]);

export const batchVerifyResponseSchema = z.object({
  ok: z.boolean(),
  trust_level: trustLevel,
  build: z.object({ ok: z.boolean() }).passthrough(),
  axiom_audit: z
    .object({
      ok: z.boolean(),
      trust_level: trustLevel,
      blocked_reasons: z.array(z.string()).optional(),
    })
    .passthrough(),
  fresh_checker: z.object({ ok: z.boolean() }).passthrough(),
  reasons: z.array(z.string()).optional(),
  axiom_evidence_real: z.boolean().optional(),
  fresh_evidence_real: z.boolean().optional(),
});

export const reviewPayloadSchema = z.object({
  thread_id: z.string(),
  obligation_id: z.string().optional(),
  status: z.string().optional(),
  reasons: z.array(z.string()).optional(),
}).passthrough();

export const resumeResponseSchema = z.object({
  ok: z.boolean(),
  thread_id: z.string(),
  artifacts_count: z.number().optional(),
}).passthrough();

export function assertBatchVerifyResponse(data: unknown): void {
  batchVerifyResponseSchema.parse(data);
}

export function assertReviewPayload(data: unknown): void {
  reviewPayloadSchema.parse(data);
}

export function assertResumeResponse(data: unknown): void {
  resumeResponseSchema.parse(data);
}
