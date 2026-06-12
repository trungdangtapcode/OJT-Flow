import type { RetrievalEvidenceBucket, RetrievalPackage } from "../../../types";
import { EvidenceReadinessHeader } from "./evidence-readiness-header";
import { EvidenceReadinessInterpretationCard } from "./evidence-readiness-interpretation-card";
import { EvidenceReadinessMissingBuckets } from "./evidence-readiness-missing-buckets";
import { evidenceReadinessShellClass } from "./evidence-readiness-shell-class";
import {
  evidenceReadinessView,
  type EvidenceReadinessFilterAction,
  type EvidenceReadinessFilterField,
} from "../model/evidence-readiness-model";

export function EvidenceReadinessPanel({
  filterFieldLabel,
  formatFilterValue,
  getBucketSuggestedFilter,
  isSearchPending,
  onApplyBucketFilter,
  packageData,
}: {
  filterFieldLabel: (field: EvidenceReadinessFilterField) => string;
  formatFilterValue: (field: EvidenceReadinessFilterField, value: string) => string;
  getBucketSuggestedFilter: (
    bucket: RetrievalEvidenceBucket,
  ) => EvidenceReadinessFilterAction | null;
  isSearchPending: boolean;
  onApplyBucketFilter: (field: EvidenceReadinessFilterField, value: string) => void;
  packageData: RetrievalPackage;
}) {
  const {
    bucketSignalAction,
    interpretation,
    missingBuckets,
    qualitySummary,
    ready,
  } = evidenceReadinessView(packageData);
  return (
    <div className={evidenceReadinessShellClass(ready)}>
      <EvidenceReadinessHeader
        missingBucketCount={missingBuckets.length}
        qualitySummary={qualitySummary}
        ready={ready}
      />
      <EvidenceReadinessMissingBuckets
        filterFieldLabel={filterFieldLabel}
        formatFilterValue={formatFilterValue}
        getBucketSuggestedFilter={getBucketSuggestedFilter}
        isSearchPending={isSearchPending}
        missingBuckets={missingBuckets}
        onApplyBucketFilter={onApplyBucketFilter}
      />
      <EvidenceReadinessInterpretationCard
        interpretation={interpretation}
        qualitySummary={qualitySummary}
      />
      <div className="break-words text-sm leading-6 text-muted-foreground">
        {bucketSignalAction ??
          qualitySummary?.top_action ??
          "Review selected evidence before using it downstream."}
      </div>
    </div>
  );
}
