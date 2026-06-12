import type {
  ConceptGroundingSummary,
  QueryAspectSummary,
  RetrievalCoverageSummary,
} from "./retrieval-run-summary";

export type RetrievalQueryAspectComparison = {
  added: QueryAspectSummary[];
  removed: QueryAspectSummary[];
  retained: QueryAspectSummary[];
};

export type RetrievalConceptGroundingComparison = {
  added: ConceptGroundingSummary[];
  removed: ConceptGroundingSummary[];
  retained: ConceptGroundingSummary[];
};

export type RetrievalCoverageComparison = {
  added: RetrievalCoverageSummary[];
  improved: RetrievalCoverageStatusChange[];
  regressed: RetrievalCoverageStatusChange[];
  removed: RetrievalCoverageSummary[];
  retained: RetrievalCoverageSummary[];
};

export type RetrievalCoverageStatusChange = {
  active: RetrievalCoverageSummary;
  baseline: RetrievalCoverageSummary;
};

export type RetrievalQualitySignalComparison = {
  added: RetrievalQualitySignalSummary[];
  removed: RetrievalQualitySignalSummary[];
  retained: RetrievalQualitySignalSummary[];
};

export type RetrievalQualitySignalSummary = {
  code: string;
  message: string;
  severity: string;
  suggestedAction: string;
};
