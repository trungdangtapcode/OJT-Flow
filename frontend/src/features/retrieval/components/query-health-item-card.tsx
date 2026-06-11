import { ListFilter, X } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import { queryHealthBadgeVariant } from "./query-health-status";
import type { QueryHealthFilterEntry, QueryHealthItem } from "./search-cockpit-panel-types";

export function QueryHealthItemCard({
  activeFilters,
  isSearchPending,
  item,
  onClearAllFilters,
  onClearSourceScope,
}: {
  activeFilters: QueryHealthFilterEntry[];
  isSearchPending: boolean;
  item: QueryHealthItem;
  onClearAllFilters: () => void;
  onClearSourceScope: () => void;
}) {
  const sourceFilter = activeFilters.find((filter) => filter.field === "source_id");
  return (
    <div className="grid gap-1 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="break-words font-black">{item.label}</span>
        <Badge variant={queryHealthBadgeVariant(item.status)}>
          {humanize(item.status)}
        </Badge>
      </div>
      <div className="break-words text-xs leading-5 text-muted-foreground">
        {item.description}
      </div>
      {item.code === "diagnostic_overconstrained_metadata_filters" ? (
        <div className="flex min-w-0 flex-wrap gap-1.5 pt-1">
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
      ) : null}
    </div>
  );
}
