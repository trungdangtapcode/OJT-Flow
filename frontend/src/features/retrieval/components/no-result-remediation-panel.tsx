import { NoResultLoosenScopeCard } from "./no-result-loosen-scope-card";
import { NoResultQualityCard } from "./no-result-quality-card";
import { NoResultRemediationHeader } from "./no-result-remediation-header";
import { NoResultSuggestionCard } from "./no-result-suggestion-card";
import type {
  NoResultActiveFilter,
  NoResultFilterField,
  NoResultSuggestedAction,
} from "./no-result-remediation-types";

export function NoResultRemediationPanel({
  candidateCount,
  filterFieldLabel,
  isSearchPending,
  missingBucketCount,
  onApplyFacet,
  onClearAllFilters,
  onClearFilter,
  submittedFilters,
  suggestedAction,
}: {
  candidateCount: number;
  filterFieldLabel: (field: NoResultFilterField) => string;
  isSearchPending: boolean;
  missingBucketCount: number;
  onApplyFacet: (field: NoResultFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearFilter: (field: NoResultFilterField) => void;
  submittedFilters: NoResultActiveFilter[];
  suggestedAction: NoResultSuggestedAction | null;
}) {
  return (
    <div className="grid gap-3 rounded-md border border-amber-200 bg-amber-50 p-4">
      <NoResultRemediationHeader
        candidateCount={candidateCount}
        missingBucketCount={missingBucketCount}
        submittedFilters={submittedFilters}
      />
      <div className="grid gap-2 md:grid-cols-3">
        <NoResultLoosenScopeCard
          isSearchPending={isSearchPending}
          onClearAllFilters={onClearAllFilters}
          onClearFilter={onClearFilter}
          submittedFilters={submittedFilters}
        />
        <NoResultQualityCard candidateCount={candidateCount} />
        <NoResultSuggestionCard
          filterFieldLabel={filterFieldLabel}
          isSearchPending={isSearchPending}
          onApplyFacet={onApplyFacet}
          suggestedAction={suggestedAction}
        />
      </div>
    </div>
  );
}
