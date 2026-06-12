import type * as React from "react";

import type { SearchPlanPreviewPanel } from "../components/search-plan-preview-panel";
import {
  formatMaybeSupportedFilterValue,
  isSupportedFilterField,
} from "./retrieval-filter-model";
import { formatCount } from "./retrieval-format";
import type { RetrievalPagePropsArgs } from "./retrieval-page-prop-types";

export function retrievalPageSearchPlanPreviewProps({
  searchMutation,
  workspace,
}: RetrievalPagePropsArgs): React.ComponentProps<typeof SearchPlanPreviewPanel> {
  return {
    currentPlanData: workspace.planSession.currentPlanData,
    currentPlanPayload: workspace.planSession.currentPlanPayload,
    formatCount,
    formatFilterValue: formatMaybeSupportedFilterValue,
    isPlanLoading: workspace.planSession.isPlanLoading,
    isSearchPending: searchMutation.isPending,
    isSupportedFilterField,
    onApplyFilterSuggestion: workspace.searchActions.applyPlanFilterSuggestion,
    onRunTask: workspace.searchActions.runPlannedTask,
    packageData: workspace.planSession.packageDataForPlanPreview,
    planError: workspace.planSession.planError,
    submittedSearchPayload: workspace.runSession.submittedSearchPayload,
  };
}
