import { humanize } from "../../../lib/utils";
import { supportStatusBadgeVariant } from "../model/retrieval-evidence-model";
import {
  bucketSuggestedFilter,
  filterFieldLabel,
  formatFilterValue,
} from "../model/retrieval-filter-model";
import { formatCount, formatScore } from "../model/retrieval-format";
import {
  judgmentBadgeVariant,
  judgmentLabel,
} from "../model/retrieval-judgment-model";
import { EvidencePackBuckets } from "./evidence-pack-buckets";
import { EvidenceReadinessPanel } from "./evidence-readiness-panel";
import { EvidenceSupportMatrix } from "./evidence-support-matrix";
import { ResultFacets } from "./result-facets";
import type { SearchResultsSharedProps } from "./search-results-section-types";

export function SearchResultsEvidenceSection({
  isSearchPending,
  onApplyFacet,
  packageData,
  view,
}: SearchResultsSharedProps) {
  return (
    <>
      <EvidenceReadinessPanel
        filterFieldLabel={filterFieldLabel}
        formatFilterValue={formatFilterValue}
        getBucketSuggestedFilter={bucketSuggestedFilter}
        isSearchPending={isSearchPending}
        onApplyBucketFilter={onApplyFacet}
        packageData={packageData}
      />
      <EvidencePackBuckets buckets={packageData.evidence_buckets ?? []} />
      <EvidenceSupportMatrix
        formatCount={formatCount}
        formatScore={formatScore}
        humanize={humanize}
        judgmentBadgeVariant={judgmentBadgeVariant}
        judgmentLabel={judgmentLabel}
        rows={view.supportMatrixRows}
        supportStatusBadgeVariant={supportStatusBadgeVariant}
      />
      <ResultFacets
        activeFilters={view.resultFilters}
        facets={packageData.facets}
        isSearchPending={isSearchPending}
        onApplyFacet={onApplyFacet}
      />
    </>
  );
}
