import type { RetrievalComparisonDiagnosticInput } from "./retrieval-comparison-diagnosis-types";

export type RetrievalComparisonRecommendedAction = {
  action: string;
  priority: number;
  reason: string;
  severity: "success" | "warning" | "destructive" | "muted";
  source: string;
};

export type RetrievalComparisonRecommendedActionSummary = {
  action_count: number;
  badge_variant: "success" | "warning" | "destructive";
  highest_priority: number | null;
  highest_severity: "success" | "warning" | "destructive";
  source_count: number;
  source_counts: Record<string, number>;
  sources: string[];
};

export type RetrievalComparisonRecommendationInput =
  RetrievalComparisonDiagnosticInput & {
    activeSummary: {
      qualitySummary: {
        status: string;
        top_action?: string | null;
      } | null;
    };
    metrics: {
      churnRate: number;
      overlapRatio: number;
    };
    qualityWarningDelta: number;
  };
