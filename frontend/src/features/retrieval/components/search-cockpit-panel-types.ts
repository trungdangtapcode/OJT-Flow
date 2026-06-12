export type QueryHealthStatus = "ok" | "review" | "blocked" | "info";

export type QueryHealthItem = {
  code: string;
  description: string;
  label: string;
  status: QueryHealthStatus;
};

export type SearchReadinessChecklistItem = {
  code: string;
  detail: string;
  label: string;
  status: QueryHealthStatus;
};

export type QueryHealthFilterEntry = {
  field: string;
};
