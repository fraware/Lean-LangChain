export type PolicyDecision = {
  decision: "accepted" | "rejected" | "blocked" | "needs_review" | "lower_trust" | "failed";
  trust_level: "clean" | "warning" | "blocked";
  reasons: string[];
};
