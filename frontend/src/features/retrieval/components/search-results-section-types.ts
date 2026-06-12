import type {
  Evidence,
  RetrievalJudgmentEvaluationResult,
  RetrievalPackage,
  RetrievalRelevanceJudgmentSummary,
  RetrievalSearchPayload,
} from "../../../types";
import type {
  ActiveFacetFilters,
  SupportedFilterField,
} from "../model/retrieval-filter-model";
import type {
  RelevanceJudgmentIndex,
  RelevanceJudgmentValue,
} from "../model/retrieval-judgment-model";
import type { searchResultsViewModel } from "../model/search-results-view-model";

export type SearchResultsView = ReturnType<typeof searchResultsViewModel>;

export type SearchResultsSharedProps = {
  activeFilters: ActiveFacetFilters;
  isSearchPending: boolean;
  isStale: boolean;
  onApplyFacet: (field: SupportedFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearFilter: (field: SupportedFilterField) => void;
  packageData: RetrievalPackage;
  submittedSearchPayload: RetrievalSearchPayload | null;
  view: SearchResultsView;
};

export type SearchResultsJudgmentProps = {
  isJudgmentSyncing: boolean;
  packageData: RetrievalPackage;
  persistedJudgmentEvaluation: RetrievalJudgmentEvaluationResult | null;
  persistedJudgmentSummary: RetrievalRelevanceJudgmentSummary | null;
  view: SearchResultsView;
};

export type SearchResultsHitsProps = {
  isSearchPending: boolean;
  onApplyFacet: (field: SupportedFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearFilter: (field: SupportedFilterField) => void;
  onSetJudgment: (evidence: Evidence, value: RelevanceJudgmentValue) => void;
  packageData: RetrievalPackage;
  relevanceJudgments: RelevanceJudgmentIndex;
  runId: string | null;
  submittedSearchPayload: RetrievalSearchPayload | null;
};
