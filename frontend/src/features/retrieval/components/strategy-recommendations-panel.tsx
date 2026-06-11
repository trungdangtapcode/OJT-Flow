import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { RetrievalStrategyRecommendation } from "../../../types";
import { formatCount } from "./strategy-standard-format";
import { StrategyRecommendationCard } from "./strategy-recommendation-card";
import type { SearchPlanFilterAction, SearchPlanFilterField } from "./strategy-standard-types";

export function StrategyRecommendationsPanel({
  getSuggestedFilterAction,
  isSearchPending,
  onApplyFilter,
  recommendations,
}: {
  getSuggestedFilterAction: (value: unknown) => SearchPlanFilterAction | null;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
  recommendations: RetrievalStrategyRecommendation[];
}) {
  if (!recommendations.length) {
    return null;
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
          Strategy recommendations
          <HelpTooltip label="Strategy recommendations help">
            Backend-generated search advice. Apply a recommendation only when it matches the operational question and the suggested filter is supported.
          </HelpTooltip>
        </div>
        <Badge variant="muted">{formatCount(recommendations.length, "rule")}</Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        {recommendations.slice(0, 4).map((recommendation) => (
          <StrategyRecommendationCard
            getSuggestedFilterAction={getSuggestedFilterAction}
            isSearchPending={isSearchPending}
            key={recommendation.recommendation_id}
            onApplyFilter={onApplyFilter}
            recommendation={recommendation}
          />
        ))}
      </div>
    </div>
  );
}
