export type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export type RunComparisonOperatorSummaryView = {
  bullets: string[];
  headline: string;
  reviewFocus: string[];
  status: "stable" | "review" | "improved";
};

export type RunComparisonDiagnosisView = {
  code: string;
  message: string;
  severity: "success" | "warning" | "muted";
};

export type RunComparisonRecommendedActionView = {
  action: string;
  priority: number;
  reason: string;
  severity: BadgeVariant;
  source: string;
};

export type RunComparisonRecommendedActionSummaryView = {
  action_count: number;
  badge_variant: "success" | "warning" | "destructive";
  highest_priority: number | null;
  highest_severity: "success" | "warning" | "destructive";
  source_count: number;
  source_counts: Record<string, number>;
  sources: string[];
};

export type RunComparisonMetricsView = {
  changedRankCount: number;
  churnRate: number;
  meanAbsoluteRankDelta: number;
  overlapRatio: number;
  sharedCount: number;
  unionCount: number;
};

export type RunComparisonAtAGlanceView = {
  metrics: Pick<RunComparisonMetricsView, "churnRate" | "overlapRatio">;
  qualitySummaryChanged: boolean;
  sourceDiversityComparison: {
    duplicateSelectedSourceDelta: number;
    selectedSourceDelta: number;
  };
  topSourceChanged: boolean;
};
