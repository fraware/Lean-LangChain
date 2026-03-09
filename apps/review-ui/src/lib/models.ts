export type ReviewPayload = {
  thread_id: string;
  obligation_id: string;
  status: "awaiting_review" | "approved" | "rejected";
};
