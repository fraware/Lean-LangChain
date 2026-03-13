import type { ReviewPayload } from "@/lib/models";

export function AxiomAuditPanel({ payload }: { payload: ReviewPayload }) {
  const audit = payload.axiom_audit_summary;
  const hasAudit = audit && typeof audit === "object" && Object.keys(audit).length > 0;
  return (
    <div className="border rounded p-4">
      <h2>Axiom audit</h2>
      {hasAudit ? (
        <pre className="text-xs overflow-auto max-h-40 bg-gray-100 dark:bg-gray-800 p-2 rounded">
          {JSON.stringify(audit, null, 2)}
        </pre>
      ) : (
        <p className="text-gray-500">No axiom audit data.</p>
      )}
    </div>
  );
}
