import { Badge } from "../../../components/ui/badge";
import type { RetrievalSearchCockpitView } from "../model/retrieval-cockpit-view-model";
import { SearchCockpitApplyAction } from "./search-cockpit-apply-action";
import { SearchCockpitBroadenControls } from "./search-cockpit-broaden-controls";
import { cockpitCountLabel } from "./search-cockpit-format";
import type { SearchPlanFilterField } from "./strategy-standard-panels";

export function SearchCockpitNextBestAction({
  filterFieldLabel,
  isSearchPending,
  onApplyFilter,
  onClearAllFilters,
  onClearSourceScope,
  view,
}: {
  filterFieldLabel: (field: SearchPlanFilterField) => string;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearSourceScope: () => void;
  view: RetrievalSearchCockpitView;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Next best action
        </div>
        {view.correctiveActionCount !== null ? (
          <Badge variant={view.correctiveActionCount ? "warning" : "success"}>
            {cockpitCountLabel(view.correctiveActionCount, "action")}
          </Badge>
        ) : null}
      </div>
      <div className="break-words text-sm font-black">
        {view.topAction?.title ??
          view.qualitySummary?.topAction ??
          "No corrective action required"}
      </div>
      <div className="break-words text-sm leading-6 text-muted-foreground">
        {view.topAction?.description ??
          "Review the ranked evidence, source provenance, and judgment metrics before using the package downstream."}
      </div>
      <SearchCockpitApplyAction
        filterFieldLabel={filterFieldLabel}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilter}
        view={view}
      />
      <SearchCockpitBroadenControls
        isSearchPending={isSearchPending}
        onClearAllFilters={onClearAllFilters}
        onClearSourceScope={onClearSourceScope}
        view={view}
      />
    </div>
  );
}
