import type { ReviewPayload } from "@/lib/models";

type Props = {
  threadId: string;
  status: ReviewPayload["status"];
  onApprove: () => void;
  onReject: () => void;
  onResume: () => void;
  disabled: boolean;
  resumeLoading?: boolean;
};

export function ApprovalActions({
  threadId,
  status,
  onApprove,
  onReject,
  onResume,
  disabled,
  resumeLoading = false,
}: Props) {
  if (status === "approved") {
    return (
      <div className="border rounded p-4 space-y-2">
        <div className="text-green-600">Approved.</div>
        <button
          type="button"
          onClick={onResume}
          disabled={resumeLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {resumeLoading ? "Resuming…" : "Resume run"}
        </button>
      </div>
    );
  }
  if (status === "rejected") {
    return (
      <div className="border rounded p-4 space-y-2">
        <div className="text-red-600">Rejected.</div>
        <button
          type="button"
          onClick={onResume}
          disabled={resumeLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          {resumeLoading ? "Resuming…" : "Resume run"}
        </button>
      </div>
    );
  }
  return (
    <div className="border rounded p-4 flex gap-4">
      <button
        type="button"
        onClick={onApprove}
        disabled={disabled}
        className="px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50"
      >
        Approve
      </button>
      <button
        type="button"
        onClick={onReject}
        disabled={disabled}
        className="px-4 py-2 bg-red-600 text-white rounded disabled:opacity-50"
      >
        Reject
      </button>
    </div>
  );
}
