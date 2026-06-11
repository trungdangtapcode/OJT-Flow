import type { RetrievalQualitySummary } from "../../../types";

export type CorrectiveActionSummaryView = {
  actionTypeCounts: Record<string, number>;
  count: number;
  highestPriority: number | null;
  topActionTitle: string | null;
};

export type SearchRunSummaryView = {
  correctiveActionSummary: CorrectiveActionSummaryView;
  hitCount: number;
  qualitySummary: RetrievalQualitySummary | null;
  qualityWarningCount: number;
  remediationSummary: string | null;
  warningCount: number;
};
