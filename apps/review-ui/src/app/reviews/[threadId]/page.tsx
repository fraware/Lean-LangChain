"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { fetchReview, submitApproval, submitReject, submitResume } from "@/lib/api";
import type { ReviewPayload } from "@/lib/models";
import { ObligationSummary } from "@/components/review/ObligationSummary";
import { DiffPanel } from "@/components/review/DiffPanel";
import { DiagnosticsPanel } from "@/components/review/DiagnosticsPanel";
import { AxiomAuditPanel } from "@/components/review/AxiomAuditPanel";
import { PolicyDecisionPanel } from "@/components/review/PolicyDecisionPanel";
import { ApprovalActions } from "@/components/review/ApprovalActions";

export default function ReviewPage() {
  const params = useParams();
  const router = useRouter();
  const threadId = typeof params.threadId === "string" ? params.threadId : "";
  const [payload, setPayload] = useState<ReviewPayload | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeResult, setResumeResult] = useState<{ status?: string; artifacts_count?: number } | null>(null);

  const load = useCallback(async () => {
    if (!threadId) return;
    setError(null);
    try {
      const data = await fetchReview(threadId);
      setPayload(data ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPayload(null);
    }
  }, [threadId]);

  useEffect(() => {
    load();
  }, [load]);

  const onApprove = useCallback(async () => {
    if (!threadId) return;
    setError(null);
    try {
      await submitApproval(threadId);
      setPayload((p) => (p ? { ...p, status: "approved" } : p));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [threadId]);

  const onReject = useCallback(async () => {
    if (!threadId) return;
    setError(null);
    try {
      await submitReject(threadId);
      setPayload((p) => (p ? { ...p, status: "rejected" } : p));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [threadId]);

  const onResume = useCallback(async () => {
    if (!threadId) return;
    setError(null);
    setResumeLoading(true);
    try {
      const result = await submitResume(threadId);
      setPayload((p) =>
        p ? { ...p, status: "resumed" as ReviewPayload["status"], _resumeResult: result } : p
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setResumeLoading(false);
    }
  }, [threadId]);

  if (payload === undefined) {
    return (
      <main className="p-6">
        <p>Loading review...</p>
      </main>
    );
  }

  if (payload === null) {
    return (
      <main className="p-6">
        <h1>Review not found</h1>
        <p>No pending review for thread {threadId}.</p>
        <button type="button" onClick={() => router.back()}>
          Back
        </button>
      </main>
    );
  }

  const canAct = payload.status === "awaiting_review";

  return (
    <main className="p-6 max-w-4xl mx-auto space-y-6">
      <h1>Review: {threadId}</h1>
      {error && <div className="text-red-600">{error}</div>}
      <ObligationSummary payload={payload} />
      <DiffPanel payload={payload} />
      <DiagnosticsPanel payload={payload} />
      <AxiomAuditPanel payload={payload} />
      <PolicyDecisionPanel payload={payload} />
      <ApprovalActions
        threadId={threadId}
        status={payload.status}
        onApprove={onApprove}
        onReject={onReject}
        onResume={onResume}
        disabled={!canAct}
        resumeLoading={resumeLoading}
      />
      {resumeResult && (
        <div className="border rounded p-4 text-green-600">
          Run resumed. Status: {resumeResult.status ?? "—"}. Artifacts: {resumeResult.artifacts_count ?? 0}.
        </div>
      )}
    </main>
  );
}
