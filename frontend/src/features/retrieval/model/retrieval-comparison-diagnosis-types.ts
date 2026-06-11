export type RetrievalComparisonDiagnosis = {
  code: string;
  message: string;
  severity: "success" | "warning" | "muted";
};

export type RetrievalComparisonDiagnosticInput = {
  addedEvidenceIds: string[];
  conceptGroundingComparison: {
    added: unknown[];
    removed: unknown[];
  };
  coverageComparison: {
    added: unknown[];
    improved: unknown[];
    regressed: unknown[];
  };
  facetComparisons: Array<{
    activeCount: number;
    addedValues: string[];
    baselineCount: number;
    field: string;
    label: string;
    removedValues: string[];
    retainedValues: string[];
  }>;
  qualityScoreDelta: number | null;
  qualitySignalComparison: {
    added: unknown[];
    removed: unknown[];
  };
  qualitySummaryChanged: boolean;
  queryAspectComparison: {
    added: unknown[];
    removed: unknown[];
  };
  queryProfileChanged: boolean;
  rankChanges: unknown[];
  removedEvidenceIds: string[];
  rulePackChanged: boolean;
  sourceDiversityComparison: {
    candidateSourceDelta: number;
    duplicateSelectedSourceDelta: number;
    lambdaChanged: boolean;
    selectedSourceDelta: number;
    selectionModeChanged: boolean;
    sourceOverlapRatio: number;
  };
  topSourceChanged: boolean;
};
