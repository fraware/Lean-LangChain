import type { ReviewPayload } from "@/lib/models";

export function DiagnosticsPanel({ payload }: { payload: ReviewPayload }) {
  const diagnostics = payload.diagnostics_summary;
  const list = Array.isArray(diagnostics) ? diagnostics : diagnostics && typeof diagnostics === "object" ? Object.entries(diagnostics) : [];
  return (
    <div className="border rounded p-4">
      <h2>Diagnostics</h2>
      {list.length > 0 ? (
        <pre className="text-xs overflow-auto max-h-40 bg-gray-100 dark:bg-gray-800 p-2 rounded">
          {JSON.stringify(diagnostics, null, 2)}
        </pre>
      ) : (
        <p className="text-gray-500">No diagnostics.</p>
      )}
    </div>
  );
}
