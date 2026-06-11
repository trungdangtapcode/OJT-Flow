import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type {
  RetrievalJudgmentEvaluationResult,
  RetrievalRelevanceJudgmentSummary,
} from "../../../types";
import { JudgmentEvaluationBadges } from "./judgment-evaluation-badges";
import { JudgmentEvaluationCopyAction } from "./judgment-evaluation-copy-action";
import type { RelevanceJudgmentMetricsView } from "./judgment-evaluation-types";

export function JudgmentEvaluationHeader({
  copyEvaluationReport,
  evaluationCopied,
  evaluationReportJson,
  formatCount,
  isSyncing,
  metrics,
  persistedEvaluation,
  persistedSummary,
}: {
  copyEvaluationReport: () => Promise<void>;
  evaluationCopied: boolean;
  evaluationReportJson: string | null;
  formatCount: (count: number, singular: string, plural?: string) => string;
  isSyncing: boolean;
  metrics: RelevanceJudgmentMetricsView;
  persistedEvaluation: RetrievalJudgmentEvaluationResult | null;
  persistedSummary: RetrievalRelevanceJudgmentSummary | null;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
      <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
        Judgment metrics
        <HelpTooltip label="Judgment metrics help">
          Metrics summarize how many ranked hits have human relevance labels and how useful the current ranking looks for this query.
        </HelpTooltip>
      </div>
      <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
        <JudgmentEvaluationBadges
          formatCount={formatCount}
          isSyncing={isSyncing}
          metrics={metrics}
          persistedEvaluation={persistedEvaluation}
          persistedSummary={persistedSummary}
        />
        <JudgmentEvaluationCopyAction
          copyEvaluationReport={copyEvaluationReport}
          evaluationCopied={evaluationCopied}
          evaluationReportJson={evaluationReportJson}
        />
      </div>
    </div>
  );
}
