import type { RetrievalPackage } from "../../../types";
import { primaryRecommendedAction } from "./retrieval-review-actions";
import type {
  RetrievalReviewCheck,
  RetrievalReviewGuidance,
} from "./retrieval-review-types";

export function retrievalReviewGuidance(
  packageData: RetrievalPackage,
  checklist: RetrievalReviewCheck[],
): RetrievalReviewGuidance {
  const blockedCount = checklist.filter((item) => item.status === "blocked").length;
  const reviewCount = checklist.filter((item) => item.status === "review").length;
  const interpretation = packageData.interpretation ?? null;
  const primaryAction = primaryRecommendedAction(packageData);
  if (blockedCount > 0 || !packageData.hits.length) {
    return {
      actionDetail:
        primaryAction?.description ??
        "Broaden the query, clear restrictive filters, or reindex trusted sources before relying on this retrieval package.",
      actionTitle: primaryAction?.title ?? "Fix search coverage",
      badge: "blocked",
      description:
        interpretation?.summary ??
        "The search package is missing evidence needed for a reliable operational review.",
      headline:
        packageData.remediation_summary ??
        "Do not use this retrieval package as final support yet.",
      status: "blocked",
    };
  }
  if (reviewCount > 0) {
    return {
      actionDetail:
        primaryAction?.description ??
        "Review warnings, required support, and top-hit score drivers before accepting the evidence order.",
      actionTitle: primaryAction?.title ?? "Review before accepting",
      badge: "review",
      description:
        interpretation?.summary ??
        "Evidence was found, but at least one quality or coverage check still needs operator review.",
      headline:
        packageData.remediation_summary ??
        "Use this result with review because quality checks raised follow-up work.",
      status: "review",
    };
  }
  return {
    actionDetail:
      primaryAction?.description ??
      "Inspect the top evidence and record relevance feedback if the result supports the workflow question.",
    actionTitle: primaryAction?.title ?? "Review top evidence",
    badge: "ready",
    description:
      interpretation?.summary ??
      "The package has ranked evidence, covered required support, and no retrieval warnings.",
    headline:
      packageData.remediation_summary ??
      "This retrieval package is ready for operator evidence review.",
    status: "ok",
  };
}
