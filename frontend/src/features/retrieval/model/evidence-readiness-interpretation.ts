import { humanize } from "../../../lib/utils";
import type { RetrievalQualitySummary } from "../../../types";
import type { EvidenceReadinessInterpretation } from "./evidence-readiness-types";

export function readinessInterpretation(
  qualitySummary: RetrievalQualitySummary | null,
  missingRequiredBucketCount: number,
): EvidenceReadinessInterpretation {
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

export function qualitySummaryBadgeVariant(
  summary: RetrievalQualitySummary,
): "success" | "warning" | "destructive" | "muted" {
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  if (summary.status === "review") return "warning";
  return "muted";
}
