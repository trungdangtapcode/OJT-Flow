import { Badge } from "../../../components/ui/badge";
import { QueryAspectPlanCard } from "./query-aspect-plan-card";
import type {
  QueryAspectFilterApplyHandler,
  QueryAspectPlanItemView,
} from "./query-aspect-plan-types";
import { TokenList } from "./token-list";
export type {
  QueryAspectFilterEntryView,
  QueryAspectPlanItemView,
} from "./query-aspect-plan-types";

export function QueryAspectPlan({
  aspects,
  formatCount,
  isSearchPending,
  onApplyFilter,
}: {
  aspects: QueryAspectPlanItemView[];
  formatCount: (count: number, singular: string) => string;
  isSearchPending: boolean;
  onApplyFilter: QueryAspectFilterApplyHandler;
}) {
  if (!aspects.length) {
    return <TokenList items={[]} title="Search aspect plan" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Search aspect plan
        </div>
        <Badge variant="muted">{formatCount(aspects.length, "aspect")}</Badge>
      </div>
      <div className="grid gap-2">
        {aspects.map((aspect) => (
          <QueryAspectPlanCard
            aspect={aspect}
            isSearchPending={isSearchPending}
            key={aspect.aspectId}
            onApplyFilter={onApplyFilter}
          />
        ))}
      </div>
    </div>
  );
}
