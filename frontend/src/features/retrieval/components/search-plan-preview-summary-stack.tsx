import {
  SearchPlanCoverageSummaryPanel,
  SearchPlanTaskSummaryPanel,
} from "./search-plan-summary-panels";
import { SearchPlanRouteDecisionPanel } from "./search-plan-route-decision-panel";
import { SearchPlanPreviewNotices } from "./search-plan-preview-notices";
import type { SearchPlanPreviewProps } from "./search-plan-preview-types";

type SearchPlanPreviewSummaryStackProps = Pick<
  SearchPlanPreviewProps,
  | "copyTextToClipboard"
  | "formatCount"
  | "isPlanLoading"
  | "isSearchPending"
  | "onRunTask"
  | "planError"
  | "qualitySummaryBadgeVariant"
  | "useCopyFeedback"
> & {
  view: NonNullable<SearchPlanPreviewProps["view"]>;
};

export function SearchPlanPreviewSummaryStack({
  copyTextToClipboard,
  formatCount,
  isPlanLoading,
  isSearchPending,
  onRunTask,
  planError,
  qualitySummaryBadgeVariant,
  useCopyFeedback,
  view,
}: SearchPlanPreviewSummaryStackProps) {
  const {
    analysis,
    coverageSummary,
    planSummary,
    profile,
    qualitySummary,
    taskSummary,
  } = view;

  return (
    <>
      <SearchPlanRouteDecisionPanel
        analysis={analysis}
        formatCount={formatCount}
        planSummary={planSummary}
        profile={profile}
        qualitySummary={qualitySummary}
        qualitySummaryBadgeVariant={qualitySummaryBadgeVariant}
      />

      <SearchPlanPreviewNotices
        isPlanLoading={isPlanLoading}
        isSearchPending={false}
        planError={planError}
        showPlanningNotice={!qualitySummary}
      />

      <SearchPlanCoverageSummaryPanel summary={coverageSummary} />
      <SearchPlanTaskSummaryPanel
        copyTextToClipboard={copyTextToClipboard}
        isSearchPending={isSearchPending}
        onRunTask={onRunTask}
        summary={taskSummary}
        tasks={analysis.retrievalTasks}
        useCopyFeedback={useCopyFeedback}
      />
    </>
  );
}
