import type { ReviewPayload } from "@/lib/models";

export function DiffPanel({ payload }: { payload: ReviewPayload }) {
  const patch = payload.patch_metadata as { current_patch?: Record<string, string> } | undefined;
  const current = patch?.current_patch;
  return (
    <div className="border rounded p-4">
      <h2>Patch / diff</h2>
      {payload.diff_summary ? (
        <pre className="text-sm whitespace-pre-wrap font-mono">{payload.diff_summary}</pre>
      ) : current && Object.keys(current).length > 0 ? (
        <pre className="text-xs overflow-auto max-h-60 bg-gray-100 dark:bg-gray-800 p-2 rounded font-mono">
          {Object.entries(current).map(([path, content]) => `=== ${path }\n${content}`).join("\n\n")}
        </pre>
      ) : (
        <p className="text-gray-500">No patch or diff.</p>
      )}
    </div>
  );
}
