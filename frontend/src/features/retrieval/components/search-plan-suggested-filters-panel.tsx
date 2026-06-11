import { Badge } from "../../../components/ui/badge";
import type { FilterSuggestionStack } from "./search-plan-detail-panels";
import { SearchPlanFilterSuggestionPreview } from "./search-plan-detail-panels";
import { SectionHelpText } from "./section-help-text";

type SupportedPlanFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export function SearchPlanSuggestedFiltersPanel({
  filterSuggestions,
  formatCount,
  formatFilterValue,
  isSearchPending,
  isSupportedFilterField,
  onApplyFilterSuggestion,
}: {
  filterSuggestions: FilterSuggestionStack[];
  formatCount: (count: number, singular: string) => string;
  formatFilterValue: (field: SupportedPlanFilterField, value: string) => string;
  isSearchPending: boolean;
  isSupportedFilterField: (field: string) => field is SupportedPlanFilterField;
  onApplyFilterSuggestion: (suggestion: FilterSuggestionStack) => void;
}) {
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Suggested filters
        </span>
        <Badge variant={filterSuggestions.length ? "warning" : "success"}>
          {filterSuggestions.length
            ? formatCount(filterSuggestions.length, "suggestion")
            : "none"}
        </Badge>
      </div>
      {filterSuggestions.length ? (
        <div className="grid gap-1.5">
          {filterSuggestions.slice(0, 4).map((suggestion) => (
            <SearchPlanFilterSuggestionPreview
              displayValue={
                isSupportedFilterField(suggestion.field)
                  ? formatFilterValue(suggestion.field, suggestion.value)
                  : suggestion.value
              }
              isSearchPending={isSearchPending}
              key={`${suggestion.field}-${suggestion.value}-${suggestion.reason}`}
              onApplySuggestion={onApplyFilterSuggestion}
              suggestion={suggestion}
              supported={isSupportedFilterField(suggestion.field)}
            />
          ))}
        </div>
      ) : (
        <SectionHelpText>
          No additional metadata filters were suggested for this query.
        </SectionHelpText>
      )}
    </div>
  );
}
