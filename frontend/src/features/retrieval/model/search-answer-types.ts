export type SearchAnswerStatus = {
  label: string;
  variant: "default" | "success" | "warning" | "destructive" | "muted";
};

export type SearchAnswerMetric = {
  detail: string;
  label: string;
  value: string;
};

export type SearchAnswerViewModel = {
  actionCount: number;
  metrics: SearchAnswerMetric[];
  qualityScore: number | null;
  remediation: string;
  report: Record<string, unknown>;
  status: SearchAnswerStatus;
  warnings: string[];
};
