import type { RetrievalSearchPayload, RuntimeRetrievalRulePack } from "../../../types";
import type { SearchRunSummaryView } from "./search-run-presentation";
import type { RetrievalComparisonDiagnosis } from "./retrieval-comparison-diagnosis-types";
import type { RetrievalComparisonRecommendationInput } from "./retrieval-comparison-recommendation-types";

export type RetrievalComparisonReportInput =
  RetrievalComparisonRecommendationInput & {
    activePayload: RetrievalSearchPayload;
    activeQuery: string;
    activeRunId: string;
    activeSubmittedAt: string;
    activeSummary: SearchRunSummaryView & {
      queryProfile?: unknown;
      serverSignature?: string | null;
    };
    baselinePayload: RetrievalSearchPayload;
    baselineQuery: string;
    baselineRunId: string;
    baselineSubmittedAt: string;
    baselineSummary: SearchRunSummaryView & {
      queryProfile?: unknown;
      serverSignature?: string | null;
    };
    candidateDelta: number;
    conceptGroundingComparison: {
      added: unknown[];
      removed: unknown[];
      retained: unknown[];
    };
    coverageComparison: {
      added: unknown[];
      improved: unknown[];
      regressed: unknown[];
      removed: unknown[];
      retained: unknown[];
    };
    diagnosis: RetrievalComparisonDiagnosis[];
    facetComparisons: Array<{
      activeCount: number;
      addedValues: string[];
      baselineCount: number;
      field: string;
      label: string;
      removedValues: string[];
      retainedValues: string[];
    }>;
    hitDelta: number;
    metrics: {
      churnRate: number;
      overlapRatio: number;
      [key: string]: unknown;
    };
    queryAspectComparison: {
      added: unknown[];
      removed: unknown[];
      retained: unknown[];
    };
    qualityScoreDelta: number | null;
    qualitySignalComparison: {
      added: unknown[];
      removed: unknown[];
      retained: unknown[];
    };
    rankChanges: unknown[];
    retainedEvidenceIds: string[];
    rulePackChanges: Array<{
      active?: RuntimeRetrievalRulePack;
      baseline?: RuntimeRetrievalRulePack;
      name: string;
      status: string;
    }>;
    sourceDiversityComparison: RetrievalComparisonRecommendationInput["sourceDiversityComparison"] & {
      active: {
        candidateSourceCount: number;
        duplicateSelectedSourceCount: number;
        enabled: boolean;
        lambda: number | null;
        selectedSourceCount: number;
        selectionMode: string;
      };
      activeSelectedSourceIds: string[];
      addedSourceIds: string[];
      baseline: {
        candidateSourceCount: number;
        duplicateSelectedSourceCount: number;
        enabled: boolean;
        lambda: number | null;
        selectedSourceCount: number;
        selectionMode: string;
      };
      baselineSelectedSourceIds: string[];
      removedSourceIds: string[];
      retainedSourceIds: string[];
      sourceOverlapRatio: number;
    };
    topSourceAfter: string | null;
    topSourceBefore: string | null;
    warningDelta: number;
  };
