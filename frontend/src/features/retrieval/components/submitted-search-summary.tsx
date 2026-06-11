import type { RetrievalSearchPayload } from "../../../types";
import type { ActiveFilterBarEntry } from "./active-filter-bar";
import { SubmittedSearchFilterChips } from "./submitted-search-filter-chips";
import { SubmittedSearchMetadataChips } from "./submitted-search-metadata-chips";
import { SubmittedSearchSummaryHeader } from "./submitted-search-summary-header";

export function SubmittedSearchSummary({
  filters,
  isRestoreDisabled,
  isStale,
  onRestore,
  payload,
}: {
  filters: ActiveFilterBarEntry[];
  isRestoreDisabled: boolean;
  isStale: boolean;
  onRestore: () => void;
  payload: RetrievalSearchPayload;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <SubmittedSearchSummaryHeader
        isRestoreDisabled={isRestoreDisabled}
        isStale={isStale}
        onRestore={onRestore}
      />
      <div className="grid gap-2 text-sm">
        <div className="break-words font-semibold">{payload.query}</div>
        <SubmittedSearchMetadataChips payload={payload} />
        <SubmittedSearchFilterChips filters={filters} />
      </div>
    </div>
  );
}
