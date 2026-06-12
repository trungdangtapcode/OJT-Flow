import { ListFilter, X } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { NoResultActionCard } from "./no-result-action-card";
import type {
  NoResultActiveFilter,
  NoResultFilterField,
} from "./no-result-remediation-types";

export function NoResultLoosenScopeCard({
  isSearchPending,
  onClearAllFilters,
  onClearFilter,
  submittedFilters,
}: {
  isSearchPending: boolean;
  onClearAllFilters: () => void;
  onClearFilter: (field: NoResultFilterField) => void;
  submittedFilters: NoResultActiveFilter[];
}) {
  const sourceFilter = submittedFilters.find((filter) => filter.field === "source_id");

  return (
    <NoResultActionCard
      text={
        submittedFilters.length
          ? "The submitted search has active filters. Remove exact source, standard, domain, or trust filters if you need broader evidence."
          : "Try fewer exact terms, add field names, or start from a trusted preset when the query is too narrow."
      }
      title={submittedFilters.length ? "Loosen scope" : "Broaden query"}
    >
      {submittedFilters.length ? (
        <div className="grid gap-2">
          <div className="flex min-w-0 flex-wrap gap-1.5">
            {submittedFilters.map((filter) => (
              <Badge className="max-w-full break-words" key={filter.field} variant="muted">
                {filter.label}: {filter.displayValue}
              </Badge>
            ))}
          </div>
          <div className="flex min-w-0 flex-wrap gap-1.5">
            {sourceFilter ? (
              <Button
                disabled={isSearchPending}
                onClick={() => onClearFilter("source_id")}
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
              disabled={isSearchPending}
              onClick={onClearAllFilters}
              size="sm"
              title="Clear all active metadata filters and rerun search"
              type="button"
              variant="outline"
            >
              <ListFilter className="h-4 w-4" />
              Clear all filters
            </Button>
          </div>
        </div>
      ) : null}
    </NoResultActionCard>
  );
}
