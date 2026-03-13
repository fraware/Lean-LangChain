import type { ReviewPayload } from "@/lib/models";

export function ObligationSummary({ payload }: { payload: ReviewPayload }) {
  return (
    <div className="border rounded p-4">
      <h2>Obligation summary</h2>
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
        <dt>Thread ID</dt>
        <dd className="font-mono">{payload.thread_id}</dd>
        <dt>Obligation ID</dt>
        <dd className="font-mono">{payload.obligation_id || "—"}</dd>
        <dt>Status</dt>
        <dd>{payload.status}</dd>
      </dl>
      {payload.obligation_summary && Object.keys(payload.obligation_summary).length > 0 && (
        <pre className="mt-2 text-xs overflow-auto max-h-40 bg-gray-100 dark:bg-gray-800 p-2 rounded">
          {JSON.stringify(payload.obligation_summary, null, 2)}
        </pre>
      )}
    </div>
  );
}
