import {
  SearchPlanAspectPreview,
  SearchPlanHintPreview,
  SearchPlanRewritePreview,
} from "./search-plan-detail-panels";
import { SearchPlanRiskSignalsPanel } from "./search-plan-summary-panels";
import { SearchPlanSuggestedFiltersPanel } from "./search-plan-suggested-filters-panel";
import { SearchPlanTaskPreview } from "./search-plan-task-preview";
import type { SearchPlanPreviewProps } from "./search-plan-preview-types";

type SearchPlanPreviewDetailStackProps = Pick<
  SearchPlanPreviewProps,
  | "copyTextToClipboard"
  | "formatCount"
  | "formatFilterValue"
  | "isSearchPending"
  | "isSupportedFilterField"
  | "onApplyFilterSuggestion"
  | "onRunTask"
  | "useCopyFeedback"
> & {
  view: NonNullable<SearchPlanPreviewProps["view"]>;
};

export function SearchPlanPreviewDetailStack({
  copyTextToClipboard,
  formatCount,
  formatFilterValue,
  isSearchPending,
  isSupportedFilterField,
  onApplyFilterSuggestion,
  onRunTask,
  useCopyFeedback,
  view,
}: SearchPlanPreviewDetailStackProps) {
  const { analysis, riskSignals, variants } = view;

  return (
    <>
      <SearchPlanRiskSignalsPanel signals={riskSignals} />
      <SearchPlanTaskPreview
        copyTextToClipboard={copyTextToClipboard}
        isSearchPending={isSearchPending}
        onRunTask={onRunTask}
        tasks={analysis.retrievalTasks}
        useCopyFeedback={useCopyFeedback}
      />
      <SearchPlanAspectPreview aspects={analysis.queryAspects} />
      <SearchPlanRewritePreview variants={variants} />
      <SearchPlanHintPreview hints={analysis.searchHints} />

      <SearchPlanSuggestedFiltersPanel
        filterSuggestions={analysis.filterSuggestions}
        formatCount={formatCount}
        formatFilterValue={formatFilterValue}
        isSearchPending={isSearchPending}
        isSupportedFilterField={isSupportedFilterField}
        onApplyFilterSuggestion={onApplyFilterSuggestion}
      />
    </>
  );
}
