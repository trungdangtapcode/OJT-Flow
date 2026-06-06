import type { RetrievalPackage, RetrievalRecommendedAction } from "../../../types";
import { humanize } from "../../../lib/utils";

export type EvidenceSupportStatus = "strong" | "partial" | "weak";

export type EvidenceInterpretationCard = {
  detail: string;
  items: string[];
  label: string;
  title: string;
};

export type EvidenceInterpretationViewModel = {
  cards: EvidenceInterpretationCard[];
  status: string;
  summary: string;
  supportStatus: EvidenceSupportStatus | null;
};

export function buildEvidenceInterpretationViewModel(
  packageData: RetrievalPackage,
): EvidenceInterpretationViewModel {
  const topHit = packageData.hits[0] ?? null;
  const primaryAction = primaryRecommendedAction(packageData);
  const requiredBuckets = packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const missingRequiredBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  const warningCount = packageWarnings(packageData).length;
  const coverageItemCount =
    (packageData.coverage?.standard_system.length ?? 0) +
    (packageData.coverage?.query_aspects?.length ?? 0);
  const backend = packageData.interpretation ?? null;
  const supportStatus = supportStatusValue(
    backend?.support_status ?? topHit?.match_explanation?.support_status,
  );
  const topScoreDriver =
    backend?.top_score_driver ??
    stringFromRecord(topHit?.match_explanation, "top_score_driver") ??
    null;
  const matchedTerms = backend?.matched_terms?.length
    ? backend.matched_terms
    : topHit?.matched_terms.slice(0, 6) ?? [];
  const conceptLabels = backend?.concept_labels?.length
    ? backend.concept_labels
    : stringArrayFromRecord(topHit?.match_explanation, "concept_labels").slice(0, 4);
  const aspectLabels = backend?.aspect_labels?.length
    ? backend.aspect_labels
    : stringArrayFromRecord(topHit?.match_explanation, "aspect_labels").slice(0, 4);
  const requiredBucketCount = backend?.required_bucket_count ?? requiredBuckets.length;
  const coveredRequiredBucketCount =
    backend?.covered_required_bucket_count ??
    requiredBuckets.length - missingRequiredBuckets.length;
  const missingRequiredBucketLabels =
    backend?.missing_required_buckets?.length
      ? backend.missing_required_buckets
      : missingRequiredBuckets.map((bucket) => bucket.label);

  return {
    cards: [
      {
        detail: topScoreDriver
          ? topScoreDriver
          : matchedTerms.length
            ? `Matched terms: ${matchedTerms.join(", ")}`
            : "No ranked evidence was returned for this request.",
        items: [
          conceptLabels.length ? `Concepts: ${conceptLabels.join(", ")}` : null,
          aspectLabels.length ? `Aspects: ${aspectLabels.join(", ")}` : null,
          topHit
            ? `${formatCount(Object.keys(topHit.evidence.locator ?? {}).length, "provenance field")} / ${formatCount(topHit.score_components?.length ?? 0, "ranking signal")}`
            : null,
        ].filter((item): item is string => Boolean(item)),
        label: "Why the top result matched",
        title: backend?.top_source_id ?? topHit?.evidence.source_id ?? "No ranked result",
      },
      {
        detail: missingRequiredBucketLabels.length
          ? `Missing required support: ${missingRequiredBucketLabels.join(", ")}`
          : "The package has no missing required evidence buckets.",
        items: [
          packageData.coverage ? `${formatCount(coverageItemCount, "coverage item")} checked` : null,
          warningCount ? `${formatCount(warningCount, "warning")} raised` : null,
        ].filter((item): item is string => Boolean(item)),
        label: "Coverage",
        title: requiredBucketCount
          ? `${coveredRequiredBucketCount}/${requiredBucketCount} required buckets`
          : "No required bucket policy",
      },
      {
        detail:
          primaryAction?.description ??
          backend?.next_action_detail ??
          "Review backend interpretation and evidence details.",
        items: [
          primaryAction ? `Priority ${primaryAction.priority}` : null,
          primaryAction ? humanize(primaryAction.action_type) : null,
        ].filter((item): item is string => Boolean(item)),
        label: "Next action",
        title: primaryAction?.title ?? backend?.next_action_title ?? "Review evidence",
      },
    ],
    status: backend ? humanize(backend.status) : fallbackStatus(packageData, missingRequiredBuckets),
    summary: backend?.summary ?? fallbackSummary(packageData, missingRequiredBuckets),
    supportStatus,
  };
}

export function evidenceSupportBadgeVariant(
  status: EvidenceSupportStatus,
): "success" | "warning" | "destructive" {
  if (status === "strong") return "success";
  if (status === "partial") return "warning";
  return "destructive";
}

function fallbackStatus(
  packageData: RetrievalPackage,
  missingRequiredBuckets: RetrievalPackage["evidence_buckets"],
): string {
  if (!packageData.hits.length) return "no ranked evidence";
  if (missingRequiredBuckets?.length) return "support gaps";
  if (packageWarnings(packageData).length) return "review warnings";
  return "ready to review";
}

function fallbackSummary(
  packageData: RetrievalPackage,
  missingRequiredBuckets: RetrievalPackage["evidence_buckets"],
): string {
  const topHit = packageData.hits[0] ?? null;
  if (!topHit) {
    return "No ranked evidence was returned. Treat this as a search coverage problem until filters, source inventory, and backend warnings have been reviewed.";
  }
  if (missingRequiredBuckets?.length) {
    return `The top result is ${topHit.evidence.source_id}, but required support is missing for ${missingRequiredBuckets.map((bucket) => bucket.label).join(", ")}.`;
  }
  if (packageWarnings(packageData).length) {
    return `The package returned ${formatCount(packageData.hits.length, "ranked hit")}; warnings indicate the search may need review before the result order is trusted.`;
  }
  return `The top result is ${topHit.evidence.source_id}. Review its source provenance, score drivers, and support status before using it.`;
}

function primaryRecommendedAction(packageData: RetrievalPackage): RetrievalRecommendedAction | null {
  return [...(packageData.recommended_actions ?? [])].sort(
    (left, right) => left.priority - right.priority,
  )[0] ?? null;
}

function packageWarnings(packageData: RetrievalPackage): string[] {
  return [
    ...(packageData.trace.warnings ?? []),
    ...((packageData.coverage?.warnings ?? []) as string[]),
  ].filter((warning) => warning.trim());
}

function supportStatusValue(value: unknown): EvidenceSupportStatus | null {
  return value === "strong" || value === "partial" || value === "weak" ? value : null;
}

function stringFromRecord(record: unknown, key: string): string | null {
  if (!record || typeof record !== "object" || Array.isArray(record)) return null;
  const value = (record as Record<string, unknown>)[key];
  return typeof value === "string" && value.trim() ? value : null;
}

function stringArrayFromRecord(record: unknown, key: string): string[] {
  if (!record || typeof record !== "object" || Array.isArray(record)) return [];
  const value = (record as Record<string, unknown>)[key];
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0)
    : [];
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
