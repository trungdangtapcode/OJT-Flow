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

export type SearchResultsProps = {
  activeFilters: ActiveFacetFilters;
  isJudgmentSyncing: boolean;
  isSearchPending: boolean;
  isStale: boolean;
  onApplyFacet: (field: SupportedFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearFilter: (field: SupportedFilterField) => void;
  onRestoreSubmittedSearch: () => void;
  onSetJudgment: (evidence: Evidence, value: RelevanceJudgmentValue) => void;
  packageData: RetrievalPackage | undefined;
  persistedJudgmentEvaluation: RetrievalJudgmentEvaluationResult | null;
  persistedJudgmentSummary: RetrievalRelevanceJudgmentSummary | null;
  relevanceJudgments: RelevanceJudgmentIndex;
  runId: string | null;
  submittedSearchPayload: RetrievalSearchPayload | null;
};
