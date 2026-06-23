import { recommendedActionFilter } from "../model/retrieval-cockpit-signals";
import {
  filterFieldLabel,
  formatFilterValue,
  suggestedFilterAction,
} from "../model/retrieval-filter-model";
import { recommendedActionSourceLabel } from "../model/search-run-presentation";
import { copyTextToClipboard } from "./copy-feedback";
import { EvidenceInterpretationPanel } from "./evidence-interpretation-panel";
import { RankedEvidenceTriage } from "./ranked-evidence-triage";
import { RecommendedActionsPanel } from "./recommended-actions-panel";
import { RetrievalReviewPathPanel } from "./retrieval-review-path";
import { RetrievalSearchCockpit } from "./retrieval-search-cockpit";
import type { SearchResultsSharedProps } from "./search-results-section-types";
import { SubmittedSearchSummary } from "./submitted-search-summary";

export function SearchResultsOverviewSection({
  isSearchPending,
  isStale,
  onApplyFacet,
  onClearAllFilters,
  onClearFilter,
  packageData,
  onRestoreSubmittedSearch,
  submittedSearchPayload,
  view,
}: SearchResultsSharedProps & {
  onRestoreSubmittedSearch: () => void;
}) {
  return (
    <>
      <RankedEvidenceTriage
        view={{
          candidateCount: packageData.trace.candidates_seen,
          coveredRequiredBucketCount: view.coveredRequiredBucketCount,
          hitCount: packageData.hits.length,
          isStale,
          judgedCount: view.judgmentMetrics.judgedCount,
          qualitySummary: packageData.quality_summary ?? null,
          requiredBucketCount: view.requiredBucketCount,
        }}
      />
      <RetrievalSearchCockpit
        copyTextToClipboard={copyTextToClipboard}
        filterFieldLabel={filterFieldLabel}
        getSuggestedFilterAction={suggestedFilterAction}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFacet}
        onClearAllFilters={onClearAllFilters}
        onClearSourceScope={() => onClearFilter("source_id")}
        reportJson={view.cockpitReportJson}
        view={view.cockpitView}
      />
      <RetrievalReviewPathPanel packageData={packageData} />
      <EvidenceInterpretationPanel packageData={packageData} />
      {submittedSearchPayload ? (
        <SubmittedSearchSummary
          filters={view.resultFilterEntries}
          isRestoreDisabled={isSearchPending}
          isStale={isStale}
          onRestore={onRestoreSubmittedSearch}
          payload={submittedSearchPayload}
        />
      ) : null}
      <RecommendedActionsPanel
        activeFilters={view.resultFilterEntries}
        actions={packageData.recommended_actions ?? []}
        filterFieldLabel={filterFieldLabel}
        formatFilterValue={formatFilterValue}
        getActionFilter={recommendedActionFilter}
        getActionSourceLabel={recommendedActionSourceLabel}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFacet}
        onClearAllFilters={onClearAllFilters}
        onClearSourceScope={() => onClearFilter("source_id")}
      />
    </>
  );
}
