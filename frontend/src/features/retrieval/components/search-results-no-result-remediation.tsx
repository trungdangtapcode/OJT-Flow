import type { RetrievalPackage, RetrievalSearchPayload } from "../../../types";
import {
  activeFacetFiltersFromPayload,
  activeFilterEntries,
  filterFieldLabel,
  type SupportedFilterField,
} from "../model/retrieval-filter-model";
import { firstSupportedRecommendedAction } from "../model/retrieval-cockpit-signals";
import { NoResultRemediationPanel } from "./no-result-remediation-panel";

export function SearchResultsNoResultRemediation({
  isSearchPending,
  onApplyFacet,
  onClearAllFilters,
  onClearFilter,
  packageData,
  submittedSearchPayload,
}: {
  isSearchPending: boolean;
  onApplyFacet: (field: SupportedFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearFilter: (field: SupportedFilterField) => void;
  packageData: RetrievalPackage;
  submittedSearchPayload: RetrievalSearchPayload | null;
}) {
  return (
    <NoResultRemediationPanel
      candidateCount={packageData.trace.candidates_seen}
      filterFieldLabel={filterFieldLabel}
      isSearchPending={isSearchPending}
      missingBucketCount={(packageData.evidence_buckets ?? []).filter(
        (bucket) => bucket.required && bucket.hit_count === 0,
      ).length}
      onApplyFacet={onApplyFacet}
      onClearAllFilters={onClearAllFilters}
      onClearFilter={onClearFilter}
      submittedFilters={
        submittedSearchPayload
          ? activeFilterEntries(activeFacetFiltersFromPayload(submittedSearchPayload))
          : []
      }
      suggestedAction={firstSupportedRecommendedAction(
        packageData.recommended_actions ?? [],
      )}
    />
  );
}
