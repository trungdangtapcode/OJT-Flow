import { ListFilter } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { cn, humanize } from "../../../lib/utils";
import type {
  RetrievalEvidenceBucket,
  RetrievalPackage,
  RetrievalQualitySummary,
} from "../../../types";

export type EvidenceReadinessFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type EvidenceReadinessFilterAction = {
  field: EvidenceReadinessFilterField;
  value: string;
};

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
  const qualitySummary = packageData.quality_summary ?? null;
  const requiredBuckets = (packageData.evidence_buckets ?? []).filter(
    (bucket) => bucket.required,
  );
  const missingBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  const bucketSignal = (packageData.quality_signals ?? []).find(
    (signal) => signal.code === "missing_required_evidence_buckets",
  );
  const ready = missingBuckets.length === 0 && qualitySummary?.status !== "blocked";
  const interpretation = readinessInterpretation(qualitySummary, missingBuckets.length);
  return (
    <div
      className={cn(
        "grid gap-3 rounded-md border p-3",
        ready
          ? "border-emerald-200 bg-emerald-50"
          : "border-amber-200 bg-amber-50",
      )}
    >
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
          <Badge variant={missingBuckets.length ? "warning" : "success"}>
            {missingBuckets.length
              ? formatCount(missingBuckets.length, "required gap")
              : "required buckets covered"}
          </Badge>
        </div>
      </div>
      {missingBuckets.length ? (
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
      ) : null}
      <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2">
        <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
          <div className="break-words text-sm font-black">{interpretation.title}</div>
          <Badge variant={interpretation.variant}>{interpretation.badge}</Badge>
        </div>
        <p className="break-words text-sm leading-6 text-muted-foreground">
          {interpretation.description}
        </p>
        {qualitySummary ? (
          <div className="flex min-w-0 flex-wrap gap-1.5">
            {qualitySummary.blocker_codes.slice(0, 4).map((code) => (
              <Badge
                className="max-w-full break-words"
                key={`blocker-${code}`}
                variant="destructive"
              >
                {humanize(code)}
              </Badge>
            ))}
            {qualitySummary.warning_codes.slice(0, 4).map((code) => (
              <Badge
                className="max-w-full break-words"
                key={`warning-${code}`}
                variant="warning"
              >
                {humanize(code)}
              </Badge>
            ))}
          </div>
        ) : null}
      </div>
      <div className="break-words text-sm leading-6 text-muted-foreground">
        {bucketSignal?.suggested_action ??
          qualitySummary?.top_action ??
          "Review selected evidence before using it downstream."}
      </div>
    </div>
  );
}

function readinessInterpretation(
  qualitySummary: RetrievalQualitySummary | null,
  missingRequiredBucketCount: number,
): {
  badge: string;
  description: string;
  title: string;
  variant: "success" | "warning" | "destructive" | "muted";
} {
  if (!qualitySummary) {
    return {
      badge: "unscored",
      description:
        "No readiness score was returned. Treat the evidence as unreviewed until quality signals are available.",
      title: "Readiness score unavailable",
      variant: "muted",
    };
  }
  if (qualitySummary.status === "blocked") {
    return {
      badge: "blocked",
      description:
        "Do not use this evidence package downstream yet. Resolve blocker codes or apply backend corrective actions first.",
      title: "Blocked for governed use",
      variant: "destructive",
    };
  }
  if (qualitySummary.status === "review" || missingRequiredBucketCount > 0) {
    return {
      badge: "review",
      description:
        "Use this package only with human review. Missing required evidence, warnings, or low confidence can change the interpretation.",
      title: "Needs human review",
      variant: "warning",
    };
  }
  if (qualitySummary.status === "ready") {
    return {
      badge: "ready",
      description:
        "Required evidence classes are present. Still inspect source provenance and limitations before operational use.",
      title: "Ready for evidence review",
      variant: "success",
    };
  }
  return {
    badge: humanize(qualitySummary.status),
    description:
      "The backend returned a non-standard readiness status. Review quality signals before using the evidence package.",
    title: "Readiness requires inspection",
    variant: "muted",
  };
}

function qualitySummaryBadgeVariant(
  summary: RetrievalQualitySummary,
): "success" | "warning" | "destructive" | "muted" {
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  if (summary.status === "review") return "warning";
  return "muted";
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
