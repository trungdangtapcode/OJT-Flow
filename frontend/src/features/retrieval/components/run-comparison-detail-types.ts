export type BadgeVariant = "success" | "warning" | "muted";

export type QueryProfileSummaryView = {
  complexity: string;
  label: string;
  profileId: string;
  retrievalMode: string;
  route: string;
};

export type RunComparisonQueryProfileView = {
  activeSummary: { queryProfile: QueryProfileSummaryView | null };
  baselineSummary: { queryProfile: QueryProfileSummaryView | null };
  queryProfileChanged: boolean;
};

export type ConceptGroundingSummaryView = {
  code: string | null;
  conceptId: string;
  displayName: string;
  evidenceCount: number;
  standardSystem: string;
};

export type RetrievalConceptGroundingComparisonView = {
  added: ConceptGroundingSummaryView[];
  removed: ConceptGroundingSummaryView[];
  retained: ConceptGroundingSummaryView[];
};

export type QueryAspectSummaryView = {
  aspectId: string;
  label: string;
  priority: number;
  question: string;
  ruleId: string;
};

export type RetrievalQueryAspectComparisonView = {
  added: QueryAspectSummaryView[];
  removed: QueryAspectSummaryView[];
  retained: QueryAspectSummaryView[];
};

export type RetrievalCoverageSummaryView = {
  field: string;
  label: string;
  selectedCount: number;
  status: string;
  suggestedFilter: Record<string, string>;
  value: string;
};

export type RetrievalCoverageStatusChangeView = {
  active: RetrievalCoverageSummaryView;
  baseline: RetrievalCoverageSummaryView;
};

export type RetrievalCoverageComparisonView = {
  added: RetrievalCoverageSummaryView[];
  improved: RetrievalCoverageStatusChangeView[];
  regressed: RetrievalCoverageStatusChangeView[];
  removed: RetrievalCoverageSummaryView[];
  retained: RetrievalCoverageSummaryView[];
};

export type RetrievalQualitySignalSummaryView = {
  code: string;
  message: string;
  severity: string;
};

export type RetrievalQualitySignalComparisonView = {
  added: RetrievalQualitySignalSummaryView[];
  removed: RetrievalQualitySignalSummaryView[];
  retained: RetrievalQualitySignalSummaryView[];
};

export type RetrievalFacetComparisonView = {
  activeCount: number;
  addedValues: string[];
  baselineCount: number;
  field: string;
  label: string;
  removedValues: string[];
  retainedValues: string[];
};

export type RetrievalRankChangeView = {
  evidenceId: string;
  fromRank: number;
  rankDelta: number;
  toRank: number;
};

export type RetrievalRulePackChangeView = {
  activeFingerprint: string;
  baselineFingerprint: string;
  name: string;
  status: "added" | "removed" | "changed" | "stable";
};
