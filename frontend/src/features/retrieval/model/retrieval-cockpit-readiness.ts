import { humanize } from "../../../lib/utils";
import type {
  RetrievalEvidenceBucket,
  RetrievalPackage,
  RetrievalRecommendedAction,
} from "../../../types";
import type { RetrievalCockpitDiversityStack } from "./retrieval-cockpit-runtime";
import type { RetrievalCockpitQueryHealthItem } from "./retrieval-cockpit-query-health";
import { formatCount } from "./retrieval-format";

export type RetrievalCockpitReadinessChecklistItem = {
  code: string;
  detail: string;
  label: string;
  status: "blocked" | "info" | "ok" | "review";
};

export function searchReadinessChecklist({
  diversity,
  packageData,
  queryHealth,
  requiredBuckets,
  topAction,
}: {
  diversity: RetrievalCockpitDiversityStack;
  packageData: RetrievalPackage;
  queryHealth: RetrievalCockpitQueryHealthItem[];
  requiredBuckets: RetrievalEvidenceBucket[];
  topAction: RetrievalRecommendedAction | null;
}): RetrievalCockpitReadinessChecklistItem[] {
  const blockedHealthCount = queryHealth.filter((item) => item.status === "blocked").length;
  const reviewHealthCount = queryHealth.filter((item) => item.status === "review").length;
  const missingRequiredBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  const qualitySummary = packageData.quality_summary ?? null;
  const warningCount =
    packageData.trace.warnings.length +
    packageData.trace.safety_flags.length +
    (packageData.quality_signals ?? []).filter((signal) => signal.severity !== "info").length;

  return [
    {
      code: "query_health",
      detail:
        blockedHealthCount > 0
          ? `${formatCount(blockedHealthCount, "blocked check")} must be fixed before relying on results.`
          : reviewHealthCount > 0
            ? `${formatCount(reviewHealthCount, "review check")} need operator attention.`
            : "Query wording, context, scope, and result coverage are acceptable for inspection.",
      label: "Query health",
      status: blockedHealthCount > 0 ? "blocked" : reviewHealthCount > 0 ? "review" : "ok",
    },
    {
      code: "evidence_classes",
      detail: requiredBuckets.length
        ? `${requiredBuckets.length - missingRequiredBuckets.length}/${requiredBuckets.length} required evidence classes covered.`
        : "No required evidence-bucket policy is configured for this package.",
      label: "Evidence classes",
      status: missingRequiredBuckets.length ? "review" : "ok",
    },
    {
      code: "source_spread",
      detail: diversity.enabled
        ? `${formatCount(diversity.selectedSourceCount, "selected source")} from ${formatCount(diversity.candidateSourceCount, "candidate source")}; ${formatCount(diversity.duplicateSelectedSourceCount, "duplicate selected source")}.`
        : "Source diversity selection is disabled for this run.",
      label: "Source spread",
      status: diversity.enabled
        ? diversity.selectedSourceCount > 1 || packageData.hits.length <= 1
          ? "ok"
          : "review"
        : "review",
    },
    {
      code: "governance",
      detail: topAction
        ? `Next action: ${topAction.title}.`
        : qualitySummary
          ? `Readiness ${humanize(qualitySummary.status)} at ${qualitySummary.score}/100 with ${formatCount(warningCount, "warning signal")}.`
          : `No readiness score; ${formatCount(warningCount, "warning signal")} reported.`,
      label: "Governance",
      status:
        qualitySummary?.status === "blocked"
          ? "blocked"
          : topAction || warningCount > 0 || qualitySummary?.status === "review"
            ? "review"
            : "ok",
    },
  ];
}
