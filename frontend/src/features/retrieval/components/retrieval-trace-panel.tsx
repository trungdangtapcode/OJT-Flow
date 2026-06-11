import {
  Card,
  CardContent,
} from "../../../components/ui/card";
import { RetrievalTraceContent } from "./retrieval-trace-content";
import { RetrievalTraceHeader } from "./retrieval-trace-header";
import type { RetrievalTracePanelProps } from "./retrieval-trace-panel-types";
import { RetrievalTraceUnavailable } from "./retrieval-trace-unavailable";

export type {
  RetrievalTracePanelProps,
  RetrievalTracePanelView,
  TracePanelActiveFilter,
} from "./retrieval-trace-panel-types";

export function RetrievalTracePanel({
  activeFilters,
  filterFieldLabel,
  formatCount,
  formatFilterValue,
  getActionFilter,
  getActionSourceLabel,
  getCoverageSuggestedAction,
  getCoverageSuggestedFilter,
  isSearchPending,
  isSuggestionSupported,
  onApplyCoverageFilter,
  onApplyFilterSuggestion,
  onClearAllFilters,
  onClearSourceScope,
  view,
}: RetrievalTracePanelProps) {
  return (
    <Card className="min-w-0 overflow-hidden">
      <RetrievalTraceHeader />
      <CardContent className="grid gap-3 pt-4">
        {!view ? (
          <RetrievalTraceUnavailable />
        ) : (
          <RetrievalTraceContent
            activeFilters={activeFilters}
            filterFieldLabel={filterFieldLabel}
            formatCount={formatCount}
            formatFilterValue={formatFilterValue}
            getActionFilter={getActionFilter}
            getActionSourceLabel={getActionSourceLabel}
            getCoverageSuggestedAction={getCoverageSuggestedAction}
            getCoverageSuggestedFilter={getCoverageSuggestedFilter}
            isSearchPending={isSearchPending}
            isSuggestionSupported={isSuggestionSupported}
            onApplyCoverageFilter={onApplyCoverageFilter}
            onApplyFilterSuggestion={onApplyFilterSuggestion}
            onClearAllFilters={onClearAllFilters}
            onClearSourceScope={onClearSourceScope}
            view={view}
          />
        )}
      </CardContent>
    </Card>
  );
}
