import { CheckCircle2, ListFilter, Loader2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { FilterSuggestionStack } from "./search-plan-detail-panels";
import type {
  QueryProfileCardView,
  QueryProfileFilterEntryView,
} from "./query-profile-card-types";

export function QueryProfileFilterActions({
  filterEntries,
  isSearchPending,
  onApplyFilter,
  profile,
}: {
  filterEntries: QueryProfileFilterEntryView[];
  isSearchPending: boolean;
  onApplyFilter: (suggestion: FilterSuggestionStack) => void;
  profile: QueryProfileCardView;
}) {
  if (!filterEntries.length) return null;
  return (
    <div className="flex min-w-0 flex-wrap gap-1.5">
      {filterEntries.map((entry) =>
        entry.supported ? (
          <Button
            disabled={isSearchPending || entry.applied}
            key={`${entry.field}-${entry.value}-apply`}
            onClick={() =>
              onApplyFilter({
                applied: false,
                confidence: 1,
                field: entry.field,
                reason: `Suggested by query profile ${profile.profileId}.`,
                value: entry.value,
              })
            }
            size="sm"
            title={`Apply ${entry.label}=${entry.displayValue}`}
            type="button"
            variant={entry.applied ? "secondary" : "outline"}
          >
            {entry.applied ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : isSearchPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ListFilter className="h-4 w-4" />
            )}
            {entry.applied ? `${entry.label} applied` : `Apply ${entry.label}`}
          </Button>
        ) : (
          <Badge key={`${entry.field}-${entry.value}-unsupported`} variant="warning">
            unsupported {humanize(entry.field)}
          </Badge>
        ),
      )}
    </div>
  );
}
