import { ListFilter, X } from "lucide-react";

import { Button } from "../../../components/ui/button";
import type { RetrievalSearchCockpitView } from "../model/retrieval-cockpit-view-model";

export function SearchCockpitBroadenControls({
  isSearchPending,
  onClearAllFilters,
  onClearSourceScope,
  view,
}: {
  isSearchPending: boolean;
  onClearAllFilters: () => void;
  onClearSourceScope: () => void;
  view: RetrievalSearchCockpitView;
}) {
  if (!view.topBroadeningAction) return null;
  return (
    <div className="flex min-w-0 flex-wrap gap-1.5">
      {view.activeFilters.some((filter) => filter.field === "source_id") ? (
        <Button
          disabled={isSearchPending}
          onClick={onClearSourceScope}
          size="sm"
          title="Clear exact source scope and rerun search"
          type="button"
          variant="outline"
        >
          <X className="h-4 w-4" />
          Clear source scope
        </Button>
      ) : null}
      <Button
        disabled={isSearchPending || !view.activeFilters.length}
        onClick={onClearAllFilters}
        size="sm"
        title="Clear all active metadata filters and rerun search"
        type="button"
        variant="outline"
      >
        <ListFilter className="h-4 w-4" />
        Broaden search
      </Button>
    </div>
  );
}
