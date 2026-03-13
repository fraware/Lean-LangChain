import type { ReviewPayload } from "@/lib/models";

export function PolicyDecisionPanel({ payload }: { payload: ReviewPayload }) {
  const policy = payload.policy_summary as { decision?: string; trust_level?: string; reasons?: string[] } | undefined;
  const reasons = payload.reasons ?? policy?.reasons ?? [];
  return (
    <div className="border rounded p-4">
      <h2>Policy decision</h2>
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
        <dt>Decision</dt>
        <dd>{policy?.decision ?? "—"}</dd>
        <dt>Trust level</dt>
        <dd>{payload.trust_delta ?? policy?.trust_level ?? "—"}</dd>
      </dl>
      {reasons.length > 0 && (
        <ul className="mt-2 list-disc list-inside text-sm">
          {reasons.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
