import { Badge } from "../../../components/ui/badge";
import type {
  RetrievalJudgmentEvaluationResult,
  RetrievalRelevanceJudgmentSummary,
} from "../../../types";
import type { RelevanceJudgmentMetricsView } from "./judgment-evaluation-types";

export function JudgmentEvaluationBadges({
  formatCount,
  isSyncing,
  metrics,
  persistedEvaluation,
  persistedSummary,
}: {
  formatCount: (count: number, singular: string, plural?: string) => string;
  isSyncing: boolean;
  metrics: RelevanceJudgmentMetricsView;
  persistedEvaluation: RetrievalJudgmentEvaluationResult | null;
  persistedSummary: RetrievalRelevanceJudgmentSummary | null;
}) {
  return (
    <>
      <Badge variant={metrics.judgedCount ? "success" : "muted"}>
        {formatCount(metrics.judgedCount, "judged hit")}
      </Badge>
      {persistedSummary ? (
        <Badge variant={persistedSummary.total_count ? "success" : "muted"}>
          {formatCount(persistedSummary.total_count, "stored label")}
        </Badge>
      ) : null}
      {persistedEvaluation ? (
        <Badge variant={persistedEvaluation.judged_count ? "success" : "warning"}>
          server eval {formatCount(persistedEvaluation.judged_count, "judged")}
        </Badge>
      ) : null}
      {isSyncing ? <Badge variant="warning">syncing</Badge> : null}
    </>
  );
}
