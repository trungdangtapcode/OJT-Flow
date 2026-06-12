import { AlertTriangle } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { formatNoResultCount } from "./no-result-format";
import type { NoResultActiveFilter } from "./no-result-remediation-types";

export function NoResultRemediationHeader({
  candidateCount,
  missingBucketCount,
  submittedFilters,
}: {
  candidateCount: number;
  missingBucketCount: number;
  submittedFilters: NoResultActiveFilter[];
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2 text-sm font-black">
          <AlertTriangle className="h-4 w-4 shrink-0 text-amber-700" />
          No matching evidence returned
        </div>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">
          The backend completed the search, but no ranked evidence hit is available for this exact request. Use the remediation checks below before trusting the result as evidence absence.
        </p>
      </div>
      <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
        <Badge variant="warning">{formatNoResultCount(candidateCount, "candidate")}</Badge>
        {missingBucketCount ? (
          <Badge variant="warning">{formatNoResultCount(missingBucketCount, "required gap")}</Badge>
        ) : null}
        {submittedFilters.length ? (
          <Badge variant="muted">{formatNoResultCount(submittedFilters.length, "active filter")}</Badge>
        ) : null}
      </div>
    </div>
  );
}
