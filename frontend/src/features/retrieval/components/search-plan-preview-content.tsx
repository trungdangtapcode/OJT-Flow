import { CardContent } from "../../../components/ui/card";
import { SearchPlanPreviewDetailStack } from "./search-plan-preview-detail-stack";
import { SearchPlanPreviewNotices } from "./search-plan-preview-notices";
import { SearchPlanPreviewSummaryStack } from "./search-plan-preview-summary-stack";
import type { SearchPlanPreviewProps } from "./search-plan-preview-types";

type SearchPlanPreviewContentProps = Omit<
  SearchPlanPreviewProps,
  "onCopyPlan" | "view"
> & {
  view: NonNullable<SearchPlanPreviewProps["view"]>;
};

export function SearchPlanPreviewContent({
  copyTextToClipboard,
  formatCount,
  formatFilterValue,
  isPlanLoading,
  isSearchPending,
  isSupportedFilterField,
  onApplyFilterSuggestion,
  onRunTask,
  planError,
  qualitySummaryBadgeVariant,
  useCopyFeedback,
  view,
}: SearchPlanPreviewContentProps) {
  return (
    <CardContent className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-3 pt-4">
      <SearchPlanPreviewSummaryStack
        copyTextToClipboard={copyTextToClipboard}
        formatCount={formatCount}
        isPlanLoading={isPlanLoading}
        isSearchPending={isSearchPending}
        onRunTask={onRunTask}
        planError={planError}
        qualitySummaryBadgeVariant={qualitySummaryBadgeVariant}
        useCopyFeedback={useCopyFeedback}
        view={view}
      />

      <SearchPlanPreviewDetailStack
        copyTextToClipboard={copyTextToClipboard}
        formatCount={formatCount}
        formatFilterValue={formatFilterValue}
        isSearchPending={isSearchPending}
        isSupportedFilterField={isSupportedFilterField}
        onApplyFilterSuggestion={onApplyFilterSuggestion}
        onRunTask={onRunTask}
        useCopyFeedback={useCopyFeedback}
        view={view}
      />

      <SearchPlanPreviewNotices
        isPlanLoading={false}
        isSearchPending={isSearchPending}
        planError={null}
        showPlanningNotice={false}
      />
    </CardContent>
  );
}
