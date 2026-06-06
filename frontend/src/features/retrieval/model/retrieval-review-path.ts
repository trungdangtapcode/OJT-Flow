import type { RetrievalPackage, RetrievalRecommendedAction } from "../../../types";
import { humanize } from "../../../lib/utils";

export type RetrievalReviewCheckStatus = "ok" | "review" | "blocked";

export type RetrievalReviewCheck = {
  code: "readiness" | "required_support" | "top_hit_support" | "warnings";
  detail: string;
  label: string;
  status: RetrievalReviewCheckStatus;
};

export type RetrievalReviewGuidance = {
  actionDetail: string;
  actionTitle: string;
  badge: "ready" | "review" | "blocked";
  description: string;
  headline: string;
  status: RetrievalReviewCheckStatus;
};

export type RetrievalReviewPath = {
  candidateCount: number;
  checks: RetrievalReviewCheck[];
  guidance: RetrievalReviewGuidance;
  hitCount: number;
  primaryAction: RetrievalRecommendedAction | null;
  topSourceId: string | null;
};

export function buildRetrievalReviewPath(packageData: RetrievalPackage): RetrievalReviewPath {
  const checks = retrievalReviewChecklist(packageData);
  return {
    candidateCount: packageData.trace.candidates_seen,
    checks,
    guidance: retrievalReviewGuidance(packageData, checks),
    hitCount: packageData.hits.length,
    primaryAction: primaryRecommendedAction(packageData),
    topSourceId: packageData.hits[0]?.evidence.source_id ?? null,
  };
}

export function retrievalPackageWarnings(packageData: RetrievalPackage): string[] {
  return [
    ...(packageData.trace.warnings ?? []),
    ...((packageData.coverage?.warnings ?? []) as string[]),
  ].filter((warning) => warning.trim());
}

function retrievalReviewChecklist(packageData: RetrievalPackage): RetrievalReviewCheck[] {
  const qualitySummary = packageData.quality_summary ?? null;
  const requiredBuckets = packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const missingBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  const warnings = retrievalPackageWarnings(packageData);
  const topHit = packageData.hits[0] ?? null;
  const supportSignalCount = topHit ? topHitSupportSignalCount(topHit) : 0;

  return [
    {
      code: "readiness",
      detail: qualitySummary
        ? `${humanize(qualitySummary.status)} package, score ${qualitySummary.score}/100. ${qualitySummary.top_action}`
        : "No quality summary was returned; treat the package as needing manual review.",
      label: "Readiness",
      status: qualitySummary
        ? qualitySummary.status === "ready"
          ? "ok"
          : qualitySummary.status === "blocked"
            ? "blocked"
            : "review"
        : "review",
    },
    {
      code: "required_support",
      detail: requiredBuckets.length
        ? `${requiredBuckets.length - missingBuckets.length}/${requiredBuckets.length} required evidence buckets are covered.`
        : "No required evidence bucket policy was returned for this package.",
      label: "Required support",
      status: missingBuckets.length ? "review" : "ok",
    },
    {
      code: "top_hit_support",
      detail: topHit
        ? `${topHit.evidence.source_id} has ${formatCount(supportSignalCount, "support signal")} across terms, concepts, aspects, and provenance.`
        : "No ranked evidence was returned; review filters, corpus integrity, and query specificity.",
      label: "Top evidence",
      status: topHit ? (supportSignalCount > 0 ? "ok" : "review") : "blocked",
    },
    {
      code: "warnings",
      detail: warnings.length
        ? `${formatCount(warnings.length, "warning")} must be reviewed before using the result order.`
        : "No retrieval trace or coverage warnings were returned.",
      label: "Warnings",
      status: warnings.length ? "review" : "ok",
    },
  ];
}

function retrievalReviewGuidance(
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

function primaryRecommendedAction(packageData: RetrievalPackage) {
  return [...(packageData.recommended_actions ?? [])].sort(
    (left, right) => left.priority - right.priority,
  )[0] ?? null;
}

function topHitSupportSignalCount(hit: RetrievalPackage["hits"][number]): number {
  return (
    (hit.matched_terms ?? []).length +
    arrayLength(hit.source_locator.concept_matches) +
    arrayLength(hit.source_locator.query_aspect_matches) +
    Object.keys(hit.evidence.locator ?? {}).length +
    Object.keys(hit.source_locator ?? {}).length
  );
}

function arrayLength(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
