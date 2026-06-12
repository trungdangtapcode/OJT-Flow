import type { RetrievalPackage } from "../../../types";
import type {
  SearchResultsHitsProps,
  SearchResultsJudgmentProps,
  SearchResultsSharedProps,
  SearchResultsView,
} from "./search-results-section-types";
import type { SearchResultsProps } from "./search-results-panel-types";

export type SearchResultsContentProps = {
  hitsProps: SearchResultsHitsProps;
  judgmentProps: SearchResultsJudgmentProps;
  onRestoreSubmittedSearch: () => void;
  sharedProps: SearchResultsSharedProps;
};

export function searchResultsContentProps({
  packageData,
  props,
  view,
}: {
  packageData: RetrievalPackage;
  props: SearchResultsProps;
  view: SearchResultsView;
}): SearchResultsContentProps {
  return {
    hitsProps: {
      isSearchPending: props.isSearchPending,
      onApplyFacet: props.onApplyFacet,
      onClearAllFilters: props.onClearAllFilters,
      onClearFilter: props.onClearFilter,
      onSetJudgment: props.onSetJudgment,
      packageData,
      relevanceJudgments: props.relevanceJudgments,
      runId: props.runId,
      submittedSearchPayload: props.submittedSearchPayload,
    },
    judgmentProps: {
      isJudgmentSyncing: props.isJudgmentSyncing,
      packageData,
      persistedJudgmentEvaluation: props.persistedJudgmentEvaluation,
      persistedJudgmentSummary: props.persistedJudgmentSummary,
      view,
    },
    onRestoreSubmittedSearch: props.onRestoreSubmittedSearch,
    sharedProps: {
      activeFilters: props.activeFilters,
      isSearchPending: props.isSearchPending,
      isStale: props.isStale,
      onApplyFacet: props.onApplyFacet,
      onClearAllFilters: props.onClearAllFilters,
      onClearFilter: props.onClearFilter,
      packageData,
      submittedSearchPayload: props.submittedSearchPayload,
      view,
    },
  };
}
