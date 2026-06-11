import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalRecommendedAction } from "../../../types";
import {
  formatRecommendedActionCount,
  recommendedActionTypeCounts,
} from "../model/recommended-actions-panel-model";

export function RecommendedActionsHeader({
  actions,
}: {
  actions: RetrievalRecommendedAction[];
}) {
  const actionTypeCounts = recommendedActionTypeCounts(actions);

  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
      <div className="min-w-0">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Corrective actions
        </div>
        <div className="mt-1 break-words text-sm text-muted-foreground">
          Backend-derived next steps from retrieval quality signals.
        </div>
      </div>
      <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
        <Badge variant="warning">
          {formatRecommendedActionCount(actions.length, "action")}
        </Badge>
        {Object.entries(actionTypeCounts).map(([actionType, count]) => (
          <Badge key={actionType} variant="muted">
            {humanize(actionType)} {count}
          </Badge>
        ))}
      </div>
    </div>
  );
}
