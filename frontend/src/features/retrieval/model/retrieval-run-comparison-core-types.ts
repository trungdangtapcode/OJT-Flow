import type { RetrievalSearchPayload } from "../../../types";
import type { RetrievalComparisonDiagnosis } from "./retrieval-comparison-diagnosis";
import type {
  RetrievalConceptGroundingComparison,
  RetrievalCoverageComparison,
  RetrievalQualitySignalComparison,
  RetrievalQueryAspectComparison,
} from "./retrieval-run-comparison-change-types";
import type { RetrievalFacetComparison } from "./retrieval-run-comparison-facet-types";
import type { RetrievalRunComparisonMetrics } from "./retrieval-run-comparison-metric-types";
import type { RetrievalRankChange } from "./retrieval-run-comparison-rank-types";
import type { RetrievalRulePackChange } from "./retrieval-run-comparison-rule-pack-types";
import type { RetrievalRunSummary } from "./retrieval-run-summary";
import type {
  RetrievalSourceDiversityComparisonView,
} from "./retrieval-source-diversity-types";

export type RetrievalRunComparison = {
  addedEvidenceIds: string[];
  activePayload: RetrievalSearchPayload;
  activeQuery: string;
  activeRunId: string;
  activeSubmittedAt: string;
  activeSummary: RetrievalRunSummary;
  baselinePayload: RetrievalSearchPayload;
  baselineQuery: string;
  baselineRunId: string;
  baselineSubmittedAt: string;
  baselineSummary: RetrievalRunSummary;
  candidateDelta: number;
  conceptGroundingComparison: RetrievalConceptGroundingComparison;
  coverageComparison: RetrievalCoverageComparison;
  diagnosis: RetrievalComparisonDiagnosis[];
  facetComparisons: RetrievalFacetComparison[];
  hitDelta: number;
  metrics: RetrievalRunComparisonMetrics;
  queryAspectComparison: RetrievalQueryAspectComparison;
  qualityScoreDelta: number | null;
  qualitySummaryChanged: boolean;
  qualityWarningDelta: number;
  qualitySignalComparison: RetrievalQualitySignalComparison;
  queryProfileChanged: boolean;
  rankChanges: RetrievalRankChange[];
  removedEvidenceIds: string[];
  retainedEvidenceIds: string[];
  rulePackChanges: RetrievalRulePackChange[];
  rulePackChanged: boolean;
  sourceDiversityComparison: RetrievalSourceDiversityComparison;
  topSourceAfter: string | null;
  topSourceBefore: string | null;
  topSourceChanged: boolean;
  warningDelta: number;
};

export type RetrievalSourceDiversityComparison = RetrievalSourceDiversityComparisonView;
