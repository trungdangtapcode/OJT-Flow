import { ListFilter } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { RetrievalStrategyRecommendation } from "../../../types";
import {
  filterFieldLabel,
  strategyRecommendationVariant,
} from "./strategy-standard-format";
import type { SearchPlanFilterAction, SearchPlanFilterField } from "./strategy-standard-types";

export function StrategyRecommendationCard({
  getSuggestedFilterAction,
  isSearchPending,
  onApplyFilter,
  recommendation,
}: {
  getSuggestedFilterAction: (value: unknown) => SearchPlanFilterAction | null;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
  recommendation: RetrievalStrategyRecommendation;
}) {
  const filterAction = getSuggestedFilterAction(recommendation.suggested_filters);
  return (
    <div className="grid gap-1 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <Badge variant={strategyRecommendationVariant(recommendation.status)}>
          {humanize(recommendation.status)}
        </Badge>
        <span className="break-words font-black">{recommendation.title}</span>
      </div>
      <div className="break-words text-xs font-semibold text-muted-foreground">
        {humanize(recommendation.technique)}
      </div>
      <div className="break-words text-xs leading-5 text-muted-foreground">
        {recommendation.rationale}
      </div>
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        {recommendation.source_signal_codes.slice(0, 3).map((code) => (
          <Badge key={code} variant="muted">
            {humanize(code)}
          </Badge>
        ))}
        {filterAction ? (
          <Button
            disabled={isSearchPending}
            onClick={() => onApplyFilter(filterAction.field, filterAction.value)}
            size="sm"
            type="button"
            variant="outline"
          >
            <ListFilter className="h-4 w-4" />
            Apply {filterFieldLabel(filterAction.field)}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
