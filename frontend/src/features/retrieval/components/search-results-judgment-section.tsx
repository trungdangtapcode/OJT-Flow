import type {
  RetrievalJudgmentEvaluationResult,
  RetrievalPackage,
  RetrievalRelevanceJudgmentSummary,
} from "../../../types";
import {
  formatCount,
  formatDecimal,
  formatNullableDecimal,
  formatNullablePercent,
  formatPercent,
} from "../model/retrieval-format";
import { evaluationReportFromJudgmentSummary } from "../model/retrieval-judgment-model";
import { copyTextToClipboard } from "./copy-feedback";
import { RelevanceJudgmentSummary } from "./judgment-evaluation-panels";
import { qualitySignalBadgeVariant } from "./quality-signal-list";
import type { SearchResultsView } from "./search-results-section-types";

export function SearchResultsJudgmentSection({
  isJudgmentSyncing,
  packageData,
  persistedJudgmentEvaluation,
  persistedJudgmentSummary,
  view,
}: {
  isJudgmentSyncing: boolean;
  packageData: RetrievalPackage;
  persistedJudgmentEvaluation: RetrievalJudgmentEvaluationResult | null;
  persistedJudgmentSummary: RetrievalRelevanceJudgmentSummary | null;
  view: SearchResultsView;
}) {
  return (
    <RelevanceJudgmentSummary
      copyTextToClipboard={copyTextToClipboard}
      evaluationReportJson={
        persistedJudgmentEvaluation
          ? JSON.stringify(
              evaluationReportFromJudgmentSummary(
                persistedJudgmentEvaluation,
                view.judgmentMetrics,
                persistedJudgmentSummary,
                packageData,
              ),
              null,
              2,
            )
          : null
      }
      formatCount={formatCount}
      formatDecimal={formatDecimal}
      formatNullableDecimal={formatNullableDecimal}
      formatNullablePercent={formatNullablePercent}
      formatPercent={formatPercent}
      isSyncing={isJudgmentSyncing}
      metrics={view.judgmentMetrics}
      persistedEvaluation={persistedJudgmentEvaluation}
      persistedSummary={persistedJudgmentSummary}
      qualitySignalBadgeVariant={qualitySignalBadgeVariant}
    />
  );
}
