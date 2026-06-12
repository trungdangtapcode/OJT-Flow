import { ListFilter } from "lucide-react";

import { Button } from "../../../components/ui/button";
import type { RetrievalEvidenceBucket } from "../../../types";
import type {
  EvidenceReadinessFilterAction,
  EvidenceReadinessFilterField,
} from "../model/evidence-readiness-model";

export function EvidenceReadinessMissingBuckets({
  filterFieldLabel,
  formatFilterValue,
  getBucketSuggestedFilter,
  isSearchPending,
  missingBuckets,
  onApplyBucketFilter,
}: {
  filterFieldLabel: (field: EvidenceReadinessFilterField) => string;
  formatFilterValue: (field: EvidenceReadinessFilterField, value: string) => string;
  getBucketSuggestedFilter: (
    bucket: RetrievalEvidenceBucket,
  ) => EvidenceReadinessFilterAction | null;
  isSearchPending: boolean;
  missingBuckets: RetrievalEvidenceBucket[];
  onApplyBucketFilter: (field: EvidenceReadinessFilterField, value: string) => void;
}) {
  if (!missingBuckets.length) return null;
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {missingBuckets.map((bucket) => {
        const action = getBucketSuggestedFilter(bucket);
        return (
          <div
            className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-amber-200 bg-card px-3 py-2"
            key={bucket.bucket_id}
          >
            <div className="min-w-0">
              <div className="break-words text-sm font-black">
                Missing {bucket.label}
              </div>
              <div className="mt-1 break-words text-xs text-muted-foreground">
                {action
                  ? `${filterFieldLabel(action.field)}: ${formatFilterValue(action.field, action.value)}`
                  : "No supported filter is available for this bucket."}
              </div>
            </div>
            {action ? (
              <Button
                disabled={isSearchPending}
                onClick={() => onApplyBucketFilter(action.field, action.value)}
                size="sm"
                type="button"
                variant="outline"
              >
                <ListFilter className="h-4 w-4" />
                Apply
              </Button>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
