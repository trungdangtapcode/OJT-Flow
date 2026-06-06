import type {
  RetrievalPackage,
  RetrievalPlan,
  RetrievalSearchPayload,
} from "../../../types";
import {
  queryAnalysisFromPackage,
  queryAnalysisFromPlan,
  queryVariantsFromAnalysis,
  queryVariantsFromTrace,
  searchPlanCoverageSummary,
  searchPlanRiskSignals,
  searchPlanTaskSummary,
} from "./retrieval-query-analysis";
import { diversityFromPackage } from "./retrieval-runtime-stack";
import { serverSearchSignatureFromPackage } from "./retrieval-run-summary";

type SearchHintParameterExample = {
  example: string;
  matchedDatasetField: boolean;
  name: string;
  targetField: string;
};

type SearchHintLineageFollowup = {
  parameter: string;
  purpose: string;
};

export function retrievalSearchPlanPreviewReport(
  packageData: RetrievalPackage | undefined,
  submittedSearchPayload: RetrievalSearchPayload | null,
  planData: RetrievalPlan | undefined,
) {
  const analysis = packageData
    ? queryAnalysisFromPackage(packageData)
    : queryAnalysisFromPlan(planData!);
  return {
    report_type: "retrieval_search_plan_preview",
    version: 1,
    generated_at: new Date().toISOString(),
    submitted_payload: submittedSearchPayload,
    plan_query: planData?.query ?? null,
    search_signature: packageData
      ? serverSearchSignatureFromPackage(packageData)
      : planData?.search_signature ?? null,
    route: {
      strategy: packageData?.trace.strategy ?? analysis.strategy,
      profile: analysis.queryProfile,
      quality_summary: packageData?.quality_summary ?? null,
    },
    query_planning: {
      detected_concepts: analysis.detectedConcepts,
      standards: analysis.standards,
      rule_ids: analysis.ruleIds,
      aspects: analysis.queryAspects,
      retrieval_tasks: analysis.retrievalTasks,
      coverage_summary: searchPlanCoverageSummary(analysis),
      task_summary: searchPlanTaskSummary(analysis),
      risk_signals: searchPlanRiskSignals(analysis),
      diagnostics: analysis.diagnostics,
      filter_suggestions: analysis.filterSuggestions,
      rewrites: packageData
        ? queryVariantsFromTrace(packageData.trace)
        : queryVariantsFromAnalysis(analysis),
    },
    medical_search_hints: analysis.searchHints,
    standard_search_plan: packageData
      ? retrievalStandardSearchPlanReport(packageData)
      : null,
    trace: {
      candidates_seen: packageData?.trace.candidates_seen ?? null,
      filters_applied:
        packageData?.trace.filters_applied ?? planData?.query.filters ?? {},
      warnings: packageData?.trace.warnings ?? [],
      safety_flags: packageData?.trace.safety_flags ?? [],
    },
  };
}

export function retrievalInterpretationReport(packageData: RetrievalPackage) {
  const backendInterpretation = packageData.interpretation ?? null;
  if (backendInterpretation) {
    return {
      source: "backend",
      ...backendInterpretation,
    };
  }

  const topHit = packageData.hits[0] ?? null;
  const requiredBuckets =
    packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const missingRequiredBuckets = requiredBuckets.filter(
    (bucket) => bucket.hit_count === 0,
  );
  return {
    source: "frontend_fallback",
    status: topHit
      ? missingRequiredBuckets.length
        ? "support_gaps"
        : "ready_to_review"
      : "no_ranked_evidence",
    summary:
      packageData.remediation_summary ?? searchAnswerFallbackRemediation(packageData),
    top_evidence_id: topHit?.evidence.evidence_id ?? null,
    top_source_id: topHit?.evidence.source_id ?? null,
    top_score_driver:
      optionalStringValue(topHit?.match_explanation?.top_score_driver) ?? null,
    support_status:
      optionalStringValue(topHit?.match_explanation?.support_status) ?? null,
    matched_terms: topHit?.matched_terms.slice(0, 6) ?? [],
    concept_labels: stringArrayValue(topHit?.match_explanation?.concept_labels).slice(
      0,
      4,
    ),
    aspect_labels: stringArrayValue(topHit?.match_explanation?.aspect_labels).slice(
      0,
      4,
    ),
    required_bucket_count: requiredBuckets.length,
    covered_required_bucket_count:
      requiredBuckets.length - missingRequiredBuckets.length,
    missing_required_buckets: missingRequiredBuckets.map((bucket) => bucket.label),
    warning_count:
      (packageData.trace.warnings?.length ?? 0) +
      (packageData.coverage?.warnings?.length ?? 0),
    next_action_title: packageData.recommended_actions?.[0]?.title ?? null,
    next_action_detail: packageData.recommended_actions?.[0]?.description ?? null,
    metadata: {
      compatibility_fallback: true,
    },
  };
}

export function retrievalStandardSearchPlanReport(packageData: RetrievalPackage) {
  const plan = packageData.standard_search_plan ?? null;
  if (!plan) {
    return null;
  }
  return {
    plan_id: plan.plan_id,
    summary: plan.summary,
    primary_route: plan.primary_route,
    missing_routes: plan.missing_routes,
    governance_notes: plan.governance_notes,
    steps: plan.steps.map((step) => ({
      step_id: step.step_id,
      label: step.label,
      standard_system: step.standard_system,
      route_type: step.route_type,
      priority: step.priority,
      query: step.query,
      rationale: step.rationale,
      suggested_filters: step.suggested_filters,
      governance_notes: step.governance_notes,
      metadata: step.metadata,
    })),
  };
}

export function retrievalDiversityReport(packageData: RetrievalPackage) {
  const diversity = diversityFromPackage(packageData);
  return {
    enabled: diversity.enabled,
    selection_mode: diversity.selectionMode,
    candidate_source_count: diversity.candidateSourceCount,
    selected_source_count: diversity.selectedSourceCount,
    duplicate_selected_source_count: diversity.duplicateSelectedSourceCount,
    lambda: diversity.lambda,
    selected_hits: diversity.selectedHits.map((selection) => ({
      evidence_id: selection.evidenceId,
      source_id: selection.sourceId,
      selected_rank: selection.selectedRank,
      original_rank: selection.originalRank,
      relevance_score: selection.relevanceScore,
      redundancy_score: selection.redundancyScore,
      selection_score: selection.selectionScore,
      reason: selection.reason,
    })),
  };
}

export function medicalSearchHintReport(packageData: RetrievalPackage) {
  const analysis = queryAnalysisFromPackage(packageData);
  if (!analysis.searchHints.length) {
    return [];
  }
  return analysis.searchHints.slice(0, 8).map((hint) => {
    const metadata = hint.metadata;
    return {
      target: hint.target,
      query: hint.query,
      url: hint.url,
      rationale: hint.rationale,
      warnings: hint.warnings,
      route_details: {
        endpoint_scope: stringArrayValue(metadata.scope_endpoints).slice(0, 8),
        selected_terms: stringArrayValue(metadata.selected_terms).slice(0, 8),
        selected_unit_candidates: stringArrayValue(
          metadata.selected_unit_candidates,
        ).slice(0, 8),
        parameter_examples: searchHintParameterExamples(
          metadata.parameter_examples,
        ).slice(0, 8),
        lineage_followup: searchHintLineageFollowup(
          metadata.lineage_followup,
        ).slice(0, 4),
        launchable:
          metadata.launchable === undefined ? Boolean(hint.url) : Boolean(metadata.launchable),
        capability_warning: optionalStringValue(metadata.capability_warning),
      },
    };
  });
}

function searchAnswerFallbackRemediation(packageData: RetrievalPackage): string {
  const topAction = packageData.recommended_actions?.[0];
  if (topAction) return `${topAction.title}: ${topAction.description}`;
  const qualityAction = packageData.quality_summary?.top_action;
  if (qualityAction) return qualityAction;
  if (!packageData.hits.length) {
    return "Broaden search scope or inspect source inventory.";
  }
  return "Review the top evidence hit, readiness score, and source provenance before using this package.";
}

function searchHintParameterExamples(value: unknown): SearchHintParameterExample[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      example: stringValue(item.example, ""),
      matchedDatasetField: Boolean(item.matched_dataset_field),
      name: stringValue(item.name, ""),
      targetField: stringValue(item.target_field, ""),
    }))
    .filter((item) => item.name && item.example);
}

function searchHintLineageFollowup(value: unknown): SearchHintLineageFollowup[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      parameter: stringValue(item.parameter, ""),
      purpose: stringValue(item.purpose, ""),
    }))
    .filter((item) => item.parameter && item.purpose);
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (item): item is string => typeof item === "string" && item.trim().length > 0,
  );
}
