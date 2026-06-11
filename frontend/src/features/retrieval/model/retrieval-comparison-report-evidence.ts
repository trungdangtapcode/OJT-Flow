import type {
  RetrievalComparisonJudgmentInput,
  RetrievalComparisonReportInput,
} from "./retrieval-comparison-types";

export function comparisonJudgmentReport(
  judgments: RetrievalComparisonJudgmentInput[],
) {
  return judgments.map((judgment) => ({
    doc_id: judgment.evidenceId,
    evidence_id: judgment.evidenceId,
    judged_at: judgment.judgedAt,
    query: judgment.query,
    rating: judgment.rating,
    run_id: judgment.runId,
    value: judgment.value,
  }));
}

export function comparisonEvidenceReport(
  comparison: RetrievalComparisonReportInput,
) {
  return {
    added_ids: comparison.addedEvidenceIds,
    removed_ids: comparison.removedEvidenceIds,
    retained_ids: comparison.retainedEvidenceIds,
    rank_changes: comparison.rankChanges,
  };
}

export function comparisonRulePackReport(
  comparison: RetrievalComparisonReportInput,
) {
  return {
    changed: comparison.rulePackChanged,
    changes: comparison.rulePackChanges.map((change) => ({
      name: change.name,
      status: change.status,
      before: change.baseline ?? null,
      after: change.active ?? null,
    })),
  };
}
