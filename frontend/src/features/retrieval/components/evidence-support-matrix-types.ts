export type EvidenceSupportMatrixRowView = {
  aspectCount: number;
  bucketLabels: string[];
  conceptCount: number;
  confidenceLabel: string;
  evidenceId: string;
  judgment: { value: "relevant" | "partial" | "not_relevant" } | null;
  matchedTermCount: number;
  provenanceCount: number;
  rank: number;
  score: number;
  sourceId: string;
  sourceType: string;
  standardSystem: string | null;
  supportStatus: "strong" | "partial" | "weak";
};

export type BadgeVariant =
  | "default"
  | "success"
  | "warning"
  | "destructive"
  | "muted";

export type EvidenceSupportMatrixFormatters = {
  formatScore: (score: number) => string;
  humanize: (value: string) => string;
  judgmentBadgeVariant: (value: "relevant" | "partial" | "not_relevant") => BadgeVariant;
  judgmentLabel: (value: "relevant" | "partial" | "not_relevant") => string;
  supportStatusBadgeVariant: (
    status: EvidenceSupportMatrixRowView["supportStatus"],
  ) => BadgeVariant;
};
