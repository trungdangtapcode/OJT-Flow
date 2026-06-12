export type RetrievalCockpitQueryHealthStatus = "blocked" | "info" | "ok" | "review";

export type RetrievalCockpitQueryHealthItem = {
  code: string;
  description: string;
  label: string;
  status: RetrievalCockpitQueryHealthStatus;
};
