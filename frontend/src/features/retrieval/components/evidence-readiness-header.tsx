import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalQualitySummary } from "../../../types";
import {
  formatCount,
  qualitySummaryBadgeVariant,
} from "../model/evidence-readiness-model";

export function EvidenceReadinessHeader({
  missingBucketCount,
  qualitySummary,
  ready,
}: {
  missingBucketCount: number;
  qualitySummary: RetrievalQualitySummary | null;
  ready: boolean;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
      <div className="min-w-0">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Evidence readiness
        </div>
        <div className="mt-1 break-words text-sm font-black">
          {ready
            ? "Required evidence classes are present"
            : "Required evidence classes need review"}
        </div>
      </div>
      <div className="flex flex-wrap justify-end gap-1.5">
        {qualitySummary ? (
          <Badge variant={qualitySummaryBadgeVariant(qualitySummary)}>
            {humanize(qualitySummary.status)} {qualitySummary.score}/100
          </Badge>
        ) : null}
        <Badge variant={missingBucketCount ? "warning" : "success"}>
          {missingBucketCount
            ? formatCount(missingBucketCount, "required gap")
            : "required buckets covered"}
        </Badge>
      </div>
    </div>
  );
}
