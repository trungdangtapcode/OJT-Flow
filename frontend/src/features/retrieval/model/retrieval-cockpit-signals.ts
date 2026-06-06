import { humanize } from "../../../lib/utils";
import type {
  RetrievalEvidenceBucket,
  RetrievalPackage,
  RetrievalRecommendedAction,
  RetrievalSearchPayload,
} from "../../../types";
import type {
  RetrievalCockpitDiversityStack,
  RetrievalCockpitQueryDiagnostic,
} from "./retrieval-cockpit-runtime";
import { queryAnalysisFromPackage } from "./retrieval-cockpit-runtime";

export type RetrievalCockpitFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type RetrievalCockpitFilterAction = {
  field: RetrievalCockpitFilterField;
  value: string;
};

export type RetrievalSearchCockpitActiveFilter = {
  displayValue: string;
  field: RetrievalCockpitFilterField;
  label: string;
};

export type RetrievalCockpitQueryHealthItem = {
  code: string;
  description: string;
  label: string;
  status: "blocked" | "info" | "ok" | "review";
};

export type RetrievalCockpitReadinessChecklistItem = {
  code: string;
  detail: string;
  label: string;
  status: "blocked" | "info" | "ok" | "review";
};

export function activeFiltersFromPayload(
  payload: RetrievalSearchPayload | null,
): RetrievalSearchCockpitActiveFilter[] {
  if (!payload) return [];
  return activeFilterEntries(activeFacetFiltersFromPayload(payload));
}

export function queryHealthItems(
  payload: RetrievalSearchPayload | null,
  packageData: RetrievalPackage,
): RetrievalCockpitQueryHealthItem[] {
  const analysis = queryAnalysisFromPackage(packageData);
  const queryTerms = payload?.query.trim().split(/\s+/).filter(Boolean) ?? [];
  const fields = payload?.fields ?? [];
  const filterCount = payload ? activeFiltersFromPayload(payload).length : 0;
  const hasClinicalContext = Boolean(
    payload?.schema_id ||
      payload?.detected_format ||
      payload?.resource_type ||
      payload?.clinical_domain ||
      payload?.standard_system ||
      fields.length,
  );
  const exactSource = payload?.filters?.source_id ?? "";
  const hitCount = packageData.hits.length;
  const candidateCount = packageData.trace.candidates_seen;
  const topK = payload?.top_k ?? hitCount;
  const qualityStatus = packageData.quality_summary?.status ?? null;
  const warningCount =
    packageData.trace.warnings.length +
    packageData.trace.safety_flags.length +
    (packageData.quality_signals ?? []).filter((signal) => signal.severity !== "info").length;

  return [
    {
      code: "query_specificity",
      description:
        queryTerms.length >= 3
          ? "The query has enough wording to guide hybrid search and reranking."
          : "The query is short. Add the data type, issue, standard, or expected field names if results look broad.",
      label: "Query specificity",
      status: queryTerms.length >= 3 ? "ok" : "review",
    },
    {
      code: "clinical_context",
      description: hasClinicalContext
        ? "Schema, format, resource, domain, standard, or field context is present."
        : "No clinical data context is set. Add schema, format, resource, fields, or standard filters for safer grounding.",
      label: "Clinical context",
      status: hasClinicalContext ? "ok" : "review",
    },
    {
      code: "scope",
      description: exactSource
        ? `Exact source scope is active for ${exactSource}. Clear it before judging corpus-wide coverage.`
        : filterCount >= 3
          ? "Multiple filters are active. If evidence is sparse, loosen scope before concluding no evidence exists."
          : filterCount > 0
            ? "Some filters are active. Confirm they match the operational question."
            : "No source filters are active. This is good for discovery but may need narrowing for audit review.",
      label: "Search scope",
      status: exactSource || filterCount >= 3 ? "review" : "info",
    },
    {
      code: "result_coverage",
      description:
        hitCount === 0
          ? "No ranked evidence returned. Broaden scope, check source inventory, or apply backend recommendations."
          : hitCount < Math.min(topK, 3) && candidateCount > hitCount
            ? "Only a small ranked set survived selection. Inspect filters, readiness gaps, and reranker state."
            : `${hitCount} ranked hit(s) from ${candidateCount} candidate(s). Inspect readiness before individual claims.`,
      label: "Result coverage",
      status: hitCount === 0 ? "blocked" : hitCount < Math.min(topK, 3) ? "review" : "ok",
    },
    {
      code: "readiness",
      description: qualityStatus
        ? `Backend readiness is ${humanize(qualityStatus)}${
            packageData.quality_summary ? ` at ${packageData.quality_summary.score}/100` : ""
          }.`
        : "No readiness score returned. Treat this package as unreviewed.",
      label: "Readiness",
      status:
        qualityStatus === "ready"
          ? "ok"
          : qualityStatus === "blocked"
            ? "blocked"
            : qualityStatus
              ? "review"
              : "info",
    },
    {
      code: "safety",
      description: warningCount
        ? `${warningCount} warning or safety signal(s) were reported. Review these before using the evidence downstream.`
        : "No retrieval warnings or safety flags were reported for this package.",
      label: "Safety signals",
      status: warningCount ? "review" : "ok",
    },
    ...queryDiagnosticHealthItems(analysis.diagnostics),
  ];
}

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

export function recommendedActionFilter(
  action: RetrievalRecommendedAction,
): RetrievalCockpitFilterAction | null {
  if (action.action_type !== "apply_filter") return null;
  return suggestedFilterAction(action.suggested_filter);
}

function queryDiagnosticHealthItems(
  diagnostics: RetrievalCockpitQueryDiagnostic[],
): RetrievalCockpitQueryHealthItem[] {
  return diagnostics
    .filter((diagnostic) => diagnostic.severity !== "info")
    .map((diagnostic) => ({
      code: `diagnostic_${diagnostic.code}`,
      description: `${diagnostic.message} Action: ${diagnostic.suggestedAction}`,
      label:
        diagnostic.code === "overconstrained_metadata_filters"
          ? "Filter over-constraint"
          : humanize(diagnostic.code),
      status:
        diagnostic.severity === "error" || diagnostic.severity === "destructive"
          ? "blocked"
          : "review",
    }));
}

function activeFacetFiltersFromPayload(
  payload: RetrievalSearchPayload,
): Partial<Record<RetrievalCockpitFilterField, string>> {
  return {
    clinical_domain: payload.filters?.clinical_domain ?? payload.clinical_domain ?? undefined,
    source_id: payload.filters?.source_id ?? undefined,
    source_type: payload.filters?.source_type ?? payload.source_type ?? undefined,
    standard_system: payload.filters?.standard_system ?? payload.standard_system ?? undefined,
    trust_level: payload.filters?.trust_level ?? payload.trust_level ?? undefined,
  };
}

function activeFilterEntries(
  filters: Partial<Record<RetrievalCockpitFilterField, string>>,
): RetrievalSearchCockpitActiveFilter[] {
  return Object.entries(filters)
    .filter((entry): entry is [RetrievalCockpitFilterField, string] => Boolean(entry[1]))
    .map(([field, value]) => ({
      displayValue: humanize(value),
      field,
      label: filterFieldLabel(field),
    }));
}

function suggestedFilterAction(value: unknown): RetrievalCockpitFilterAction | null {
  const suggestedFilter = recordValue(value);
  for (const field of supportedFilterFields) {
    const filterValue = optionalStringValue(suggestedFilter[field]);
    if (filterValue) return { field, value: filterValue };
  }
  return null;
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function filterFieldLabel(field: RetrievalCockpitFilterField): string {
  const labels: Record<RetrievalCockpitFilterField, string> = {
    clinical_domain: "Domain",
    source_id: "Source",
    source_type: "Source type",
    standard_system: "Standard",
    trust_level: "Trust",
  };
  return labels[field];
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}

const supportedFilterFields: RetrievalCockpitFilterField[] = [
  "clinical_domain",
  "standard_system",
  "source_type",
  "trust_level",
  "source_id",
];
