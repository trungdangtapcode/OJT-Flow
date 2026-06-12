import { SlidersHorizontal } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { FilterSuggestionStack } from "./search-plan-detail-types";

export function SearchPlanFilterSuggestionPreview({
  displayValue,
  isSearchPending,
  onApplySuggestion,
  suggestion,
  supported,
}: {
  displayValue: string;
  isSearchPending: boolean;
  onApplySuggestion: (suggestion: FilterSuggestionStack) => void;
  suggestion: FilterSuggestionStack;
  supported: boolean;
}) {
  return (
    <div className="grid gap-1 rounded-md border border-border bg-card px-2 py-1.5 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-1.5">
        <div className="flex min-w-0 flex-wrap items-center gap-1.5">
          <Badge variant={suggestion.applied ? "success" : supported ? "muted" : "warning"}>
            {suggestion.applied ? "applied" : supported ? "available" : "unsupported"}
          </Badge>
          <span className="break-words font-black">
            {humanize(suggestion.field)}={displayValue}
          </span>
        </div>
        {supported ? (
          <Button
            disabled={isSearchPending || suggestion.applied}
            onClick={() => onApplySuggestion(suggestion)}
            size="sm"
            type="button"
            variant="outline"
          >
            <SlidersHorizontal className="h-4 w-4" />
            Apply
          </Button>
        ) : null}
      </div>
      <div className="break-words text-muted-foreground">{suggestion.reason}</div>
    </div>
  );
}
