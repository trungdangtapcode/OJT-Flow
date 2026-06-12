import type {
  RetrievalPackage,
  RetrievalPlan,
  RetrievalSearchPayload,
  RetrievalSearchTask,
} from "../../../types";
import { copyTextToClipboard, useCopyFeedback } from "./copy-feedback";
import type { FilterSuggestionStack } from "./search-plan-detail-panels";
import {
  SearchPlanPreview,
} from "./search-plan-preview";
import { useSearchPlanPreviewPanelView } from "./use-search-plan-preview-panel-view";
import { qualitySummaryBadgeVariant } from "../model/search-run-presentation";

type SupportedPlanFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export function SearchPlanPreviewPanel({
  currentPlanData,
  currentPlanPayload,
  formatCount,
  formatFilterValue,
  isPlanLoading,
  isSearchPending,
  isSupportedFilterField,
  onApplyFilterSuggestion,
  onRunTask,
  packageData,
  planError,
  submittedSearchPayload,
}: {
  currentPlanData: RetrievalPlan | undefined;
  currentPlanPayload: RetrievalSearchPayload | null;
  formatCount: (count: number, singular: string) => string;
  formatFilterValue: (field: SupportedPlanFilterField, value: string) => string;
  isPlanLoading: boolean;
  isSearchPending: boolean;
  isSupportedFilterField: (field: string) => field is SupportedPlanFilterField;
  onApplyFilterSuggestion: (suggestion: FilterSuggestionStack) => void;
  onRunTask: (task: RetrievalSearchTask) => void;
  packageData: RetrievalPackage | undefined;
  planError: string | null;
  submittedSearchPayload: RetrievalSearchPayload | null;
}) {
  const { copyPlan, view } = useSearchPlanPreviewPanelView({
    currentPlanData,
    currentPlanPayload,
    packageData,
    submittedSearchPayload,
  });

  return (
    <SearchPlanPreview
      copyTextToClipboard={copyTextToClipboard}
      formatCount={formatCount}
      formatFilterValue={formatFilterValue}
      isSearchPending={isSearchPending}
      isPlanLoading={isPlanLoading}
      isSupportedFilterField={isSupportedFilterField}
      onApplyFilterSuggestion={onApplyFilterSuggestion}
      onCopyPlan={copyPlan}
      onRunTask={onRunTask}
      planError={planError}
      qualitySummaryBadgeVariant={qualitySummaryBadgeVariant}
      useCopyFeedback={useCopyFeedback}
      view={view}
    />
  );
}
