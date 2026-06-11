import type {
  RunComparisonAtAGlanceView,
  RunComparisonDiagnosisView,
  RunComparisonMetricsView,
} from "./run-comparison-summary-panels";
import type {
  RetrievalConceptGroundingComparisonView,
  RetrievalCoverageComparisonView,
  RetrievalFacetComparisonView,
  RetrievalQualitySignalComparisonView,
  RetrievalQueryAspectComparisonView,
  RetrievalRankChangeView,
  RetrievalRulePackChangeView,
  RunComparisonQueryProfileView,
} from "./run-comparison-detail-panels";
import type { RetrievalSourceDiversityComparisonView } from "../model/retrieval-source-diversity-types";

export type BadgeVariant =
  | "default"
  | "success"
  | "warning"
  | "destructive"
  | "muted";

export type SearchRunComparisonPanelView = RunComparisonAtAGlanceView &
  RunComparisonQueryProfileView & {
    addedEvidenceIds: string[];
    baselineQuery: string;
    candidateDelta: number;
    conceptGroundingComparison: RetrievalConceptGroundingComparisonView;
    coverageComparison: RetrievalCoverageComparisonView;
    diagnosis: RunComparisonDiagnosisView[];
    facetComparisons: RetrievalFacetComparisonView[];
    hitDelta: number;
    metrics: RunComparisonMetricsView;
    queryAspectComparison: RetrievalQueryAspectComparisonView;
    qualitySignalComparison: RetrievalQualitySignalComparisonView;
    qualityWarningDelta: number;
    rankChanges: RetrievalRankChangeView[];
    removedEvidenceIds: string[];
    retainedEvidenceIds: string[];
    rulePackChanged: boolean;
    sourceDiversityComparison: RetrievalSourceDiversityComparisonView;
    topSourceAfter: string | null;
    topSourceBefore: string | null;
    warningDelta: number;
  };

export type SearchRunComparisonDetailProps = {
  comparison: SearchRunComparisonPanelView;
  formatCount: (count: number, singular: string) => string;
  rulePackChanges: RetrievalRulePackChangeView[];
};
