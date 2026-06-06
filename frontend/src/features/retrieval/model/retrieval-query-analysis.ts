import { humanize } from "../../../lib/utils";
import type {
  RetrievalPackage,
  RetrievalPlan,
  RetrievalPlanRiskSignal,
  RetrievalPlanTaskSummary,
  RetrievalQueryVariant,
  RetrievalSearchTask,
} from "../../../types";
import type {
  FilterSuggestionStack,
  QueryAspectStack,
  SearchHintStack,
} from "../components/search-plan-detail-panels";
import type { SearchPlanCoverageSummaryView } from "../components/search-plan-summary-panels";

export type QueryAnalysisStack = {
  conceptCandidates: ConceptCandidateStack[];
  detectedConcepts: string[];
  diagnostics: QueryDiagnosticStack[];
  expandedTerms: string[];
  filterSuggestions: FilterSuggestionStack[];
  queryAspects: QueryAspectStack[];
  queryProfile: QueryProfileStack | null;
  queryVariantTexts: string[];
  queryVariants: RetrievalQueryVariant[];
  planCoverageSummary: SearchPlanCoverageStack | null;
  planRiskSignals: RetrievalPlanRiskSignal[];
  planTaskSummary: RetrievalPlanTaskSummary | null;
  retrievalTasks: RetrievalSearchTask[];
  ruleIds: string[];
  searchHints: SearchHintStack[];
  standards: string[];
  strategy: string;
  variantCount: number;
};

export type SearchPlanCoverageStack = SearchPlanCoverageSummaryView;

export type QueryProfileStack = {
  complexity: string;
  description: string;
  label: string;
  profileId: string;
  retrievalMode: string;
  route: string;
  ruleIds: string[];
  suggestedFilters: Record<string, string>;
};

export type ConceptCandidateStack = {
  clinicalDomain: string | null;
  code: string | null;
  conceptId: string;
  confidence: number;
  displayName: string;
  matchedAliases: string[];
  standardSystem: string;
};

export type QueryDiagnosticStack = {
  code: string;
  metadata: Record<string, unknown>;
  message: string;
  severity: string;
  suggestedAction: string;
};

export function queryAnalysisFromPackage(packageData: RetrievalPackage): QueryAnalysisStack {
  const queryAnalysis = recordValue(packageData.handoff_context.query_analysis);
  return queryAnalysisStackFromRecord(queryAnalysis);
}

export function queryAnalysisFromPlan(planData: RetrievalPlan): QueryAnalysisStack {
  return queryAnalysisStackFromRecord(
    recordValue(planData.query_analysis),
    planCoverageSummaryValue(planData.coverage_summary),
    planTaskSummaryValue(planData.task_summary),
    planRiskSignalsValue(planData.risk_signals),
  );
}

export function searchPlanCoverageSummary(
  analysis: QueryAnalysisStack,
): SearchPlanCoverageStack {
  if (analysis.planCoverageSummary) return analysis.planCoverageSummary;
  const localTasks = analysis.retrievalTasks.filter((task) => task.target === "local_corpus");
  const externalTasks = analysis.retrievalTasks.filter(
    (task) => task.target === "external_medical_index",
  );
  const standards = uniqueValues([
    ...analysis.standards,
    ...analysis.retrievalTasks.flatMap((task) => task.standards),
  ]);
  const filterKeys = new Set<string>();
  for (const suggestion of analysis.filterSuggestions) {
    filterKeys.add(`${suggestion.field}:${suggestion.value}`);
  }
  for (const task of analysis.retrievalTasks) {
    for (const [field, value] of Object.entries(task.suggested_filters)) {
      filterKeys.add(`${field}:${value}`);
    }
  }
  const warnings = uniqueValues([
    ...analysis.diagnostics
      .filter((diagnostic) => diagnostic.severity !== "info")
      .map((diagnostic) => diagnostic.code),
    ...analysis.retrievalTasks.flatMap((task) => task.warnings),
  ]);
  const requiredLocalTaskCount = localTasks.filter((task) => task.required).length;
  const ready = requiredLocalTaskCount > 0 && standards.length > 0;
  return {
    externalTaskCount: externalTasks.length,
    filterCount: filterKeys.size,
    localTaskCount: localTasks.length,
    ready,
    requiredLocalTaskCount,
    standards,
    nextAction: fallbackPlanCoverageNextAction({
      externalTaskCount: externalTasks.length,
      filterCount: filterKeys.size,
      ready,
      requiredLocalTaskCount,
      standardCount: standards.length,
    }),
    summary: `${requiredLocalTaskCount}/${localTasks.length} required local task(s), ${externalTasks.length} external follow-up(s), ${standards.length} standard(s), and ${filterKeys.size} suggested filter(s).`,
    warnings,
  };
}

export function searchPlanTaskSummary(
  analysis: QueryAnalysisStack,
): RetrievalPlanTaskSummary {
  if (analysis.planTaskSummary) return analysis.planTaskSummary;
  const runnableLocal = analysis.retrievalTasks.filter(
    (task) => task.target === "local_corpus" && task.action_type === "run_local_search",
  );
  const requiredRunnableLocal = runnableLocal.filter((task) => task.required);
  const externalOpen = analysis.retrievalTasks.filter(
    (task) => task.target === "external_medical_index" && task.action_type === "open_external_url",
  );
  const externalCopy = analysis.retrievalTasks.filter(
    (task) => task.target === "external_medical_index" && task.action_type === "copy_query",
  );
  const blockedTasks = analysis.retrievalTasks.filter(
    (task) => !["run_local_search", "open_external_url", "copy_query"].includes(task.action_type),
  );
  const manualFollowupCount = externalOpen.length + externalCopy.length;
  return {
    total_task_count: analysis.retrievalTasks.length,
    runnable_local_count: runnableLocal.length,
    required_runnable_local_count: requiredRunnableLocal.length,
    external_open_count: externalOpen.length,
    external_copy_count: externalCopy.length,
    manual_followup_count: manualFollowupCount,
    blocked_task_count: blockedTasks.length,
    primary_action: requiredRunnableLocal.length
      ? "Run required local search tasks first, then review external follow-ups."
      : runnableLocal.length
        ? "Run the local search task, then review external follow-ups."
        : manualFollowupCount
          ? "Review external medical search follow-ups before trusting the plan."
          : "Add a more specific healthcare query before executing retrieval.",
    summary: `${runnableLocal.length} local runnable task(s), ${manualFollowupCount} external/manual follow-up(s), and ${blockedTasks.length} blocked task(s).`,
  };
}

export function searchPlanRiskSignals(
  analysis: QueryAnalysisStack,
): RetrievalPlanRiskSignal[] {
  if (analysis.planRiskSignals.length) return analysis.planRiskSignals;
  const coverage = searchPlanCoverageSummary(analysis);
  const signals: RetrievalPlanRiskSignal[] = [];
  if (!coverage.ready) {
    signals.push({
      code: "coverage_not_ready",
      message: "The plan needs more detail before review-grade search.",
      metadata: {
        local_task_count: coverage.localTaskCount,
        standard_count: coverage.standards.length,
      },
      severity: "warning",
      source: "frontend_compatibility_fallback",
      suggested_action:
        "Add a standard, field list, resource type, schema, or clinical domain before relying on the search.",
    });
  }
  signals.push(
    ...analysis.diagnostics
      .filter((diagnostic) => diagnostic.severity !== "info")
      .map((diagnostic) => ({
        code: `diagnostic_${diagnostic.code}`,
        message: diagnostic.message,
        metadata: diagnostic.metadata,
        severity: diagnostic.severity,
        source: "query_diagnostic",
        suggested_action: diagnostic.suggestedAction,
      })),
  );
  return signals.slice(0, 6);
}

export function queryVariantsFromTrace(
  trace: RetrievalPackage["trace"],
): RetrievalQueryVariant[] {
  const detailedVariants = queryVariantDetailsValue(trace.query_variant_details);
  if (detailedVariants.length) return detailedVariants;
  return trace.query_variants.map((variant) => ({
    metadata: {},
    reason: "Legacy query variant from retrieval trace.",
    source: "legacy_trace",
    variant,
  }));
}

export function queryVariantsFromAnalysis(
  analysis: QueryAnalysisStack,
): RetrievalQueryVariant[] {
  const variants = analysis.queryVariants;
  if (variants.length) return variants;
  return analysis.queryVariantTexts.map((variant) => ({
    metadata: {},
    reason: "Query variant from retrieval plan analysis.",
    source: "query_analysis",
    variant,
  }));
}

function queryAnalysisStackFromRecord(
  queryAnalysis: Record<string, unknown>,
  planCoverageSummary: SearchPlanCoverageStack | null = null,
  planTaskSummary: RetrievalPlanTaskSummary | null = null,
  planRiskSignals: RetrievalPlanRiskSignal[] = [],
): QueryAnalysisStack {
  const queryVariantTexts = stringArrayValue(queryAnalysis.query_variants);
  return {
    conceptCandidates: conceptCandidatesValue(queryAnalysis.concept_candidates),
    detectedConcepts: stringArrayValue(queryAnalysis.detected_concepts),
    diagnostics: queryDiagnosticsValue(queryAnalysis.diagnostics),
    expandedTerms: stringArrayValue(queryAnalysis.expanded_terms),
    filterSuggestions: filterSuggestionsValue(queryAnalysis.filter_suggestions),
    queryAspects: queryAspectsValue(queryAnalysis.query_aspects),
    queryProfile: queryProfileValue(queryAnalysis.query_profile),
    queryVariantTexts,
    queryVariants: queryVariantDetailsValue(queryAnalysis.query_variant_details),
    planCoverageSummary,
    planRiskSignals,
    planTaskSummary,
    retrievalTasks: retrievalTasksValue(queryAnalysis.retrieval_tasks),
    ruleIds: stringArrayValue(queryAnalysis.rule_ids),
    searchHints: searchHintsValue(queryAnalysis.search_hints),
    standards: stringArrayValue(queryAnalysis.standards),
    strategy: stringValue(queryAnalysis.strategy, "unknown"),
    variantCount: queryVariantTexts.length,
  };
}

function planTaskSummaryValue(value: unknown): RetrievalPlanTaskSummary | null {
  const summary = recordValue(value);
  const rawSummary = optionalStringValue(summary.summary);
  if (!rawSummary) return null;
  return {
    total_task_count: numberValue(summary.total_task_count) ?? 0,
    runnable_local_count: numberValue(summary.runnable_local_count) ?? 0,
    required_runnable_local_count: numberValue(summary.required_runnable_local_count) ?? 0,
    external_open_count: numberValue(summary.external_open_count) ?? 0,
    external_copy_count: numberValue(summary.external_copy_count) ?? 0,
    manual_followup_count: numberValue(summary.manual_followup_count) ?? 0,
    blocked_task_count: numberValue(summary.blocked_task_count) ?? 0,
    primary_action: stringValue(
      summary.primary_action,
      "Review the plan, then run local evidence search.",
    ),
    summary: rawSummary,
  };
}

function planCoverageSummaryValue(value: unknown): SearchPlanCoverageStack | null {
  const summary = recordValue(value);
  const rawSummary = optionalStringValue(summary.summary);
  if (!rawSummary) return null;
  return {
    externalTaskCount: numberValue(summary.external_task_count) ?? 0,
    filterCount: numberValue(summary.filter_count) ?? 0,
    localTaskCount: numberValue(summary.local_task_count) ?? 0,
    ready: booleanValue(summary.ready),
    requiredLocalTaskCount: numberValue(summary.required_local_task_count) ?? 0,
    standards: stringArrayValue(summary.standards),
    nextAction: stringValue(summary.next_action, "Review the plan, then run local evidence search."),
    summary: rawSummary,
    warnings: stringArrayValue(summary.warnings),
  };
}

function fallbackPlanCoverageNextAction({
  externalTaskCount,
  filterCount,
  ready,
  requiredLocalTaskCount,
  standardCount,
}: {
  externalTaskCount: number;
  filterCount: number;
  ready: boolean;
  requiredLocalTaskCount: number;
  standardCount: number;
}): string {
  if (!ready && standardCount === 0) {
    return "Add a healthcare standard, schema, resource type, field list, or clinical domain.";
  }
  if (!ready && requiredLocalTaskCount === 0) {
    return "Refine the query until the plan has at least one required local corpus task.";
  }
  if (filterCount > 0) return "Review suggested filters, then run the local evidence search.";
  if (externalTaskCount > 0) {
    return "Run local evidence search, then inspect external follow-up tasks if coverage is incomplete.";
  }
  return "Run local evidence search.";
}

function planRiskSignalsValue(value: unknown): RetrievalPlanRiskSignal[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      code: stringValue(item.code, ""),
      message: stringValue(item.message, "Plan risk signal unavailable."),
      metadata: recordValue(item.metadata),
      severity: stringValue(item.severity, "info"),
      source: stringValue(item.source, "plan"),
      suggested_action: stringValue(item.suggested_action, "Review this plan before running search."),
    }))
    .filter((item) => item.code);
}

function queryVariantDetailsValue(value: unknown): RetrievalQueryVariant[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      metadata: recordValue(item.metadata),
      reason: stringValue(item.reason, "Query variant used for retrieval."),
      source: stringValue(item.source, "unknown"),
      variant: stringValue(item.variant, ""),
    }))
    .filter((item) => item.variant);
}

function queryProfileValue(value: unknown): QueryProfileStack | null {
  const profile = recordValue(value);
  const profileId = stringValue(profile.profile_id, "");
  if (!profileId) return null;
  return {
    complexity: stringValue(profile.complexity, "unknown"),
    description: stringValue(profile.description, "No query profile description provided."),
    label: stringValue(profile.label, humanize(profileId)),
    profileId,
    retrievalMode: stringValue(profile.retrieval_mode, "unknown"),
    route: stringValue(profile.route, "retrieval"),
    ruleIds: stringArrayValue(profile.rule_ids),
    suggestedFilters: stringRecordValue(profile.suggested_filters),
  };
}

function queryAspectsValue(value: unknown): QueryAspectStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      aspectId: stringValue(item.aspect_id, ""),
      label: stringValue(item.label, "Search aspect"),
      priority: numberValue(item.priority) ?? 100,
      question: stringValue(item.question, "Review this search aspect."),
      rationale: stringValue(item.rationale, "Aspect generated from query analysis."),
      ruleId: stringValue(item.rule_id, ""),
      suggestedFilters: stringRecordValue(item.suggested_filters),
      suggestedTerms: stringArrayValue(item.suggested_terms),
    }))
    .filter((item) => item.aspectId)
    .sort((left, right) => left.priority - right.priority || left.label.localeCompare(right.label));
}

function retrievalTasksValue(value: unknown): RetrievalSearchTask[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => {
      const target = stringValue(item.target, "local_corpus");
      const metadata = recordValue(item.metadata);
      return {
        action_type: retrievalTaskActionTypeValue(item.action_type, target, metadata),
        aspect_id: optionalStringValue(item.aspect_id),
        label: stringValue(item.label, "Retrieval task"),
        metadata,
        priority: numberValue(item.priority) ?? 100,
        query: stringValue(item.query, ""),
        query_variants: stringArrayValue(item.query_variants),
        rationale: stringValue(item.rationale, "Generated from query analysis."),
        required: booleanValue(item.required),
        search_hint_target: optionalStringValue(item.search_hint_target),
        standards: stringArrayValue(item.standards),
        suggested_filters: stringRecordValue(item.suggested_filters),
        target: target === "external_medical_index" ? "external_medical_index" : "local_corpus",
        task_id: stringValue(item.task_id, ""),
        warnings: stringArrayValue(item.warnings),
      } satisfies RetrievalSearchTask;
    })
    .filter((item) => item.task_id && item.query)
    .sort((left, right) => left.priority - right.priority || left.label.localeCompare(right.label));
}

function retrievalTaskActionTypeValue(
  value: unknown,
  target: string,
  metadata: Record<string, unknown>,
): RetrievalSearchTask["action_type"] {
  const action = stringValue(value, "");
  if (
    action === "run_local_search" ||
    action === "open_external_url" ||
    action === "copy_query"
  ) {
    return action;
  }
  if (target === "external_medical_index") {
    return optionalStringValue(metadata.url) ? "open_external_url" : "copy_query";
  }
  return "run_local_search";
}

function conceptCandidatesValue(value: unknown): ConceptCandidateStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      clinicalDomain: optionalStringValue(item.clinical_domain),
      code: optionalStringValue(item.code),
      conceptId: stringValue(item.concept_id, "concept"),
      confidence: numberValue(item.confidence) ?? 0,
      displayName: stringValue(item.display_name, "Unknown concept"),
      matchedAliases: stringArrayValue(item.matched_aliases),
      standardSystem: stringValue(item.standard_system, "unknown"),
    }))
    .filter((item) => item.conceptId !== "concept" && item.standardSystem !== "unknown");
}

function filterSuggestionsValue(value: unknown): FilterSuggestionStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      applied: booleanValue(item.applied),
      confidence: numberValue(item.confidence) ?? 0,
      field: stringValue(item.field, "filter"),
      reason: stringValue(item.reason, "Suggested by query analysis."),
      value: stringValue(item.value, "unknown"),
    }))
    .filter((item) => item.field !== "filter" && item.value !== "unknown");
}

function queryDiagnosticsValue(value: unknown): QueryDiagnosticStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      code: stringValue(item.code, "query_diagnostic"),
      metadata: recordValue(item.metadata),
      message: stringValue(item.message, "Query diagnostic unavailable."),
      severity: stringValue(item.severity, "info"),
      suggestedAction: stringValue(item.suggested_action, "Review the retrieval query."),
    }))
    .filter((item) => item.code !== "query_diagnostic");
}

function searchHintsValue(value: unknown): SearchHintStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      metadata: recordValue(item.metadata),
      query: stringValue(item.query, ""),
      rationale: stringValue(item.rationale, "Generated from deterministic query analysis."),
      target: stringValue(item.target, "medical_search"),
      url: optionalStringValue(item.url),
      warnings: stringArrayValue(item.warnings),
    }))
    .filter((item) => item.query.length > 0 && item.target !== "medical_search");
}

function recordValue(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return value as Record<string, unknown>;
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function booleanValue(value: unknown): boolean {
  return value === true;
}

function stringArrayValue(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function stringRecordValue(value: unknown): Record<string, string> {
  const record = recordValue(value);
  return Object.fromEntries(
    Object.entries(record).filter(
      (entry): entry is [string, string] => typeof entry[1] === "string",
    ),
  );
}

function uniqueValues(values: Array<string | null | undefined>): string[] {
  return Array.from(
    new Set(values.filter((value): value is string => typeof value === "string" && value.length > 0)),
  ).sort((left, right) => left.localeCompare(right));
}
