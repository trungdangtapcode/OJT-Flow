import type {
  Evidence,
  RetrievalPackage,
  RetrievalSearchPayload,
} from "../../../types";
import {
  type SupportedFilterField,
} from "../model/retrieval-filter-model";
import {
  type RelevanceJudgmentIndex,
  type RelevanceJudgmentValue,
} from "../model/retrieval-judgment-model";
import { SearchResultsHitCardList } from "./search-results-hit-card-list";
import { SearchResultsNoResultRemediation } from "./search-results-no-result-remediation";

export function SearchResultsHitList({
  isSearchPending,
  onApplyFacet,
  onClearAllFilters,
  onClearFilter,
  onSetJudgment,
  packageData,
  relevanceJudgments,
  runId,
  submittedSearchPayload,
}: {
  isSearchPending: boolean;
  onApplyFacet: (field: SupportedFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearFilter: (field: SupportedFilterField) => void;
  onSetJudgment: (evidence: Evidence, value: RelevanceJudgmentValue) => void;
  packageData: RetrievalPackage;
  relevanceJudgments: RelevanceJudgmentIndex;
  runId: string | null;
  submittedSearchPayload: RetrievalSearchPayload | null;
}) {
  return (
    <>
      <SearchResultsHitCardList
        onSetJudgment={onSetJudgment}
        packageData={packageData}
        relevanceJudgments={relevanceJudgments}
        runId={runId}
      />
      {!packageData.hits.length ? (
        <SearchResultsNoResultRemediation
          isSearchPending={isSearchPending}
          onApplyFacet={onApplyFacet}
          onClearAllFilters={onClearAllFilters}
          onClearFilter={onClearFilter}
          packageData={packageData}
          submittedSearchPayload={submittedSearchPayload}
        />
      ) : null}
    </>
  );
}
