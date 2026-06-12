import { ListFilter, X } from "lucide-react";

import { Button } from "../../../components/ui/button";
import type { RecommendedActionActiveFilter } from "./recommended-actions-types";

export function RecommendedActionBroadenControls({
  activeFilters,
  isSearchPending,
  onClearAllFilters,
  onClearSourceScope,
}: {
  activeFilters: RecommendedActionActiveFilter[];
  isSearchPending: boolean;
  onClearAllFilters: () => void;
  onClearSourceScope: () => void;
}) {
  const sourceFilter = activeFilters.find((filter) => filter.field === "source_id");

  return (
    <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
      {sourceFilter ? (
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
        disabled={isSearchPending || !activeFilters.length}
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
