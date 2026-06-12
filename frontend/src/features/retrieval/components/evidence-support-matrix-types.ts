import type { RelevanceJudgmentValue } from "../model/retrieval-judgment-types";

export type EvidenceSupportMatrixRowView = {
  aspectCount: number;
  bucketLabels: string[];
  conceptCount: number;
  confidenceLabel: string;
  evidenceId: string;
  judgment: { value: RelevanceJudgmentValue } | null;
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
  judgmentBadgeVariant: (value: RelevanceJudgmentValue) => BadgeVariant;
  judgmentLabel: (value: RelevanceJudgmentValue) => string;
  supportStatusBadgeVariant: (
    status: EvidenceSupportMatrixRowView["supportStatus"],
  ) => BadgeVariant;
};
