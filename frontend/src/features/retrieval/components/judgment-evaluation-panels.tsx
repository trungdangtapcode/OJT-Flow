import type {
  RetrievalJudgmentEvaluationResult,
  RetrievalRelevanceJudgmentSummary,
} from "../../../types";
import { JudgmentEvaluationDetailStack } from "./judgment-evaluation-detail-stack";
import { JudgmentEvaluationHeader } from "./judgment-evaluation-header";
import {
  EvaluationReadinessPanel,
} from "./judgment-evaluation-readiness";
import type {
  BadgeVariant,
  RelevanceJudgmentMetricsView,
} from "./judgment-evaluation-types";
import { useJudgmentEvaluationReportCopy } from "./use-judgment-evaluation-report-copy";

export type { RelevanceJudgmentMetricsView } from "./judgment-evaluation-types";
export { EvaluationReadinessPanel } from "./judgment-evaluation-readiness";

export function RelevanceJudgmentSummary({
  copyTextToClipboard,
  evaluationReportJson,
  formatCount,
  formatDecimal,
  formatNullableDecimal,
  formatNullablePercent,
  formatPercent,
  isSyncing,
  metrics,
  persistedEvaluation,
  persistedSummary,
  qualitySignalBadgeVariant,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  evaluationReportJson: string | null;
  formatCount: (count: number, singular: string, plural?: string) => string;
  formatDecimal: (value: number) => string;
  formatNullableDecimal: (value: number | null) => string;
  formatNullablePercent: (value: number | null) => string;
  formatPercent: (value: number) => string;
  isSyncing: boolean;
  metrics: RelevanceJudgmentMetricsView;
  persistedEvaluation: RetrievalJudgmentEvaluationResult | null;
  persistedSummary: RetrievalRelevanceJudgmentSummary | null;
  qualitySignalBadgeVariant: (severity: string) => BadgeVariant;
}) {
  const { copyEvaluationReport, evaluationCopied } = useJudgmentEvaluationReportCopy({
    copyTextToClipboard,
    evaluationReportJson,
  });

  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3">
      <JudgmentEvaluationHeader
        copyEvaluationReport={copyEvaluationReport}
        evaluationCopied={evaluationCopied}
        evaluationReportJson={evaluationReportJson}
        formatCount={formatCount}
        isSyncing={isSyncing}
        metrics={metrics}
        persistedEvaluation={persistedEvaluation}
        persistedSummary={persistedSummary}
      />
      <JudgmentEvaluationDetailStack
        formatCount={formatCount}
        formatDecimal={formatDecimal}
        formatNullableDecimal={formatNullableDecimal}
        formatNullablePercent={formatNullablePercent}
        formatPercent={formatPercent}
        metrics={metrics}
        persistedEvaluation={persistedEvaluation}
        persistedSummary={persistedSummary}
        qualitySignalBadgeVariant={qualitySignalBadgeVariant}
      />
    </div>
  );
}
