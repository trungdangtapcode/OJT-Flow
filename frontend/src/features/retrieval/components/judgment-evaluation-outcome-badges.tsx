import { Badge } from "../../../components/ui/badge";
import type { RetrievalRelevanceJudgmentSummary } from "../../../types";
import type { RelevanceJudgmentMetricsView } from "./judgment-evaluation-types";

export function JudgmentEvaluationOutcomeBadges({
  formatCount,
  formatNullableDecimal,
  metrics,
  persistedSummary,
}: {
  formatCount: (count: number, singular: string, plural?: string) => string;
  formatNullableDecimal: (value: number | null) => string;
  metrics: RelevanceJudgmentMetricsView;
  persistedSummary: RetrievalRelevanceJudgmentSummary | null;
}) {
  if (!metrics.judgedCount) return null;

  return (
    <div className="flex min-w-0 flex-wrap gap-1.5">
      <Badge variant="success">{formatCount(metrics.relevantCount, "relevant")}</Badge>
      <Badge variant="warning">{formatCount(metrics.partialCount, "partial")}</Badge>
      <Badge variant="destructive">
        {formatCount(metrics.notRelevantCount, "not relevant")}
      </Badge>
      <Badge variant="muted">
        average rating {formatNullableDecimal(metrics.averageRating)}
      </Badge>
      {persistedSummary?.latest_updated_at ? (
        <Badge variant="muted">
          stored avg {formatNullableDecimal(persistedSummary.average_rating ?? null)}
        </Badge>
      ) : null}
    </div>
  );
}
