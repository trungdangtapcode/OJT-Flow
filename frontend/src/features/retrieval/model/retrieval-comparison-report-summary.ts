import type {
  RetrievalComparisonJudgmentInput,
  RetrievalComparisonReportInput,
} from "./retrieval-comparison-types";

export function comparisonReportSummary(
  comparison: RetrievalComparisonReportInput,
  judgments: RetrievalComparisonJudgmentInput[],
) {
  return {
    active_query: comparison.activeQuery,
    baseline_query: comparison.baselineQuery,
    status: comparison.diagnosis.some((item) => item.severity === "warning")
      ? "changed"
      : "stable",
    top_diagnosis: comparison.diagnosis[0] ?? null,
    quality: {
      before_status: comparison.baselineSummary.qualitySummary?.status ?? null,
      after_status: comparison.activeSummary.qualitySummary?.status ?? null,
      before_score: comparison.baselineSummary.qualitySummary?.score ?? null,
      after_score: comparison.activeSummary.qualitySummary?.score ?? null,
      score_delta: comparison.qualityScoreDelta,
      before_top_action: comparison.baselineSummary.qualitySummary?.top_action ?? null,
      after_top_action: comparison.activeSummary.qualitySummary?.top_action ?? null,
      changed: comparison.qualitySummaryChanged,
    },
    evidence: {
      added_count: comparison.addedEvidenceIds.length,
      removed_count: comparison.removedEvidenceIds.length,
      retained_count: comparison.retainedEvidenceIds.length,
      rank_change_count: comparison.rankChanges.length,
      top_source_changed: comparison.topSourceChanged,
    },
    top_source: {
      before: comparison.topSourceBefore,
      after: comparison.topSourceAfter,
      changed: comparison.topSourceChanged,
    },
    retrieval: {
      hit_delta: comparison.hitDelta,
      candidate_delta: comparison.candidateDelta,
      warning_delta: comparison.warningDelta,
      quality_warning_delta: comparison.qualityWarningDelta,
      overlap_ratio: comparison.metrics.overlapRatio,
      churn_ratio: comparison.metrics.churnRate,
      source_diversity: {
        selected_source_delta:
          comparison.sourceDiversityComparison.selectedSourceDelta,
        duplicate_selected_source_delta:
          comparison.sourceDiversityComparison.duplicateSelectedSourceDelta,
        source_overlap_ratio:
          comparison.sourceDiversityComparison.sourceOverlapRatio,
      },
    },
    changed_dimensions: comparison.diagnosis
      .filter((item) => item.severity !== "success")
      .map((item) => item.code),
    judgment_count: judgments.length,
  };
}
