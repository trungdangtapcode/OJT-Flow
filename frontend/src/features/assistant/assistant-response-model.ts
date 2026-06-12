import type { ComponentProps } from "react";

import type { Badge } from "../../components/ui/badge";
import type {
  AssistantEvidenceSummary,
  AssistantFinding,
  AssistantResponse,
  AssistantToolResult,
  Evidence,
  RetrievalDiversitySelection,
  RetrievalDiversitySummary,
  RetrievalEvidenceBucket,
  RetrievalStandardSearchPlan,
  RetrievalStandardSearchStep,
} from "../../types";
import {
  assistantEvidenceAnchorId,
  workflowEvidenceHref,
} from "../../lib/evidence-links";

export type AssistantBadgeVariant = ComponentProps<typeof Badge>["variant"];

export type AssistantSearchHint = {
  metadata: Record<string, unknown>;
  query: string;
  rationale: string;
  target: string;
  url: string | null;
  warnings: string[];
};

export function assistantStandardSearchMatchReasons(metadata: Record<string, unknown>) {
  const sources: {
    key: string;
    label: string;
    variant: AssistantBadgeVariant;
  }[] = [
    { key: "matched_fields", label: "field", variant: "default" },
    { key: "matched_query_aspects", label: "aspect", variant: "muted" },
    { key: "matched_standards", label: "standard", variant: "success" },
    { key: "matched_concepts", label: "concept", variant: "muted" },
    { key: "source_quality_signal_codes", label: "signal", variant: "warning" },
  ];
  return sources.flatMap((source) =>
    stringArrayValue(metadata[source.key])
      .slice(0, 3)
      .map((value) => ({
        label: source.label,
        value,
        variant: source.variant,
      })),
  );
}

export type AssistantEvidenceMatchExplanation = {
  aspectLabels: string[];
  bucketLabels: string[];
  conceptLabels: string[];
  provenanceCount: number;
  rankingSignalCount: number;
  supportStatus: "strong" | "partial" | "weak";
  topScoreDriver: string | null;
};

export type AssistantEvidenceJumpAction = {
  detail: string;
  href: string;
  label: string;
  source: "assistant" | "workflow";
};

export type AssistantReviewTaskDraft = {
  context: Record<string, unknown>;
  evidenceCount: number;
  issueCount: number;
  message: string;
  reason: string;
};

export type AssistantMappingDraft = {
  context: Record<string, unknown>;
  evidenceCount: number;
  issueCount: number;
  message: string;
  reason: string;
};

export function assistantReviewTaskDraft({
  response,
  turnContext,
  turnId,
  userMessage,
}: {
  response: AssistantResponse;
  turnContext: Record<string, unknown>;
  turnId: string;
  userMessage: string;
}): AssistantReviewTaskDraft | null {
  const issueKinds = issueKindsForResponse(response);
  const evidenceIds = evidenceIdsForResponse(response);
  const unresolvedFindings = unresolvedFindingsForResponse(response);
  if (!issueKinds.length && !evidenceIds.length && !unresolvedFindings.length) {
    return null;
  }
  const sourceWorkflowId =
    response.tool_calls
      .map(workflowIdForToolCall)
      .find((workflowId): workflowId is string => Boolean(workflowId)) ??
    optionalStringValue(turnContext.workflow_id);
  const focus = issueKinds.length
    ? `Review ${issueKinds.slice(0, 4).join(", ")} finding${issueKinds.length === 1 ? "" : "s"}`
    : "Review unresolved data quality, terminology, or evidence decision";
  const question = `${focus} from assistant turn ${turnId}.`;
  const context = {
    ...turnContext,
    review_question: question,
    assistant_review_task: {
      action: "create_review_task",
      question,
      review_focus: focus,
      source_message: userMessage,
      source_turn_id: turnId,
      source_workflow_id: sourceWorkflowId,
      issue_kinds: issueKinds,
      evidence_ids: evidenceIds,
    },
  };
  return {
    context,
    evidenceCount: evidenceIds.length,
    issueCount: issueKinds.length || unresolvedFindings.length,
    message: "Create a review task for these unresolved assistant findings.",
    reason: `${focus}. This will create durable workflow and human-review state after write confirmation.`,
  };
}

export function assistantMappingDraft({
  response,
  turnContext,
  turnId,
  userMessage,
}: {
  response: AssistantResponse;
  turnContext: Record<string, unknown>;
  turnId: string;
  userMessage: string;
}): AssistantMappingDraft | null {
  if (!optionalStringValue(turnContext.data)) return null;
  const issueKinds = issueKindsForResponse(response);
  const evidenceIds = evidenceIdsForResponse(response);
  const unresolvedFindings = unresolvedFindingsForResponse(response);
  if (!issueKinds.length && !evidenceIds.length && !unresolvedFindings.length) {
    return null;
  }
  const sourceFields = stringArrayValue(turnContext.fields);
  const targetFields = stringArrayValue(turnContext.target_fields);
  const mappingGoal = issueKinds.length
    ? `Draft a transform plan for ${issueKinds.slice(0, 4).join(", ")}`
    : "Draft a governed mapping and transformation plan";
  const instruction = `${mappingGoal} from assistant turn ${turnId}.`;
  const context = {
    ...turnContext,
    target_format: optionalStringValue(turnContext.target_format) ?? "json",
    assistant_mapping_draft: {
      action: "generate_mapping_draft",
      instruction,
      mapping_goal: mappingGoal,
      source_message: userMessage,
      source_turn_id: turnId,
      source_fields: sourceFields,
      target_fields: targetFields,
      evidence_ids: evidenceIds,
    },
  };
  return {
    context,
    evidenceCount: evidenceIds.length,
    issueCount: issueKinds.length || unresolvedFindings.length,
    message: "Generate a review-gated mapping draft for this data.",
    reason: `${mappingGoal}. This creates a draft workflow and review task without converting output yet.`,
  };
}

export function evidenceJumpActionsForSummary(
  item: AssistantEvidenceSummary,
  toolCalls: AssistantToolResult[],
): AssistantEvidenceJumpAction[] {
  const evidence = evidenceForSummary(item, toolCalls);
  if (!evidence) return [];
  return evidenceJumpActions(evidence, workflowIdForEvidence(evidence, toolCalls));
}

export function evidenceJumpActions(
  evidence: Evidence,
  workflowId: string | null = null,
): AssistantEvidenceJumpAction[] {
  const actions: AssistantEvidenceJumpAction[] = [
    {
      detail: evidenceLocatorSummary(evidence),
      href: `#${assistantEvidenceAnchorId(evidence.evidence_id)}`,
      label: "Show evidence",
      source: "assistant",
    },
  ];
  if (workflowId) {
    actions.push({
      detail: "Open persisted workflow evidence.",
      href: workflowEvidenceHref(workflowId, evidence.evidence_id),
      label: "Open workflow evidence",
      source: "workflow",
    });
  }
  return actions;
}

export function evidenceLocatorSummary(evidence: Evidence): string {
  const locator = recordValue(evidence.locator);
  const parts = [
    optionalStringValue(locator.source_ref),
    optionalStringValue(locator.section_heading),
    optionalStringValue(locator.resource_type),
    optionalStringValue(locator.standard_system),
    locator.page !== undefined ? `page ${String(locator.page)}` : null,
    locator.row !== undefined ? `row ${String(locator.row)}` : null,
    locator.column !== undefined ? `column ${String(locator.column)}` : null,
    locator.field !== undefined ? `field ${String(locator.field)}` : null,
    locator.chunk_index !== undefined ? `chunk ${String(locator.chunk_index)}` : null,
  ].filter((item): item is string => Boolean(item));
  return parts.length ? parts.slice(0, 4).join(" / ") : "Evidence locator";
}

export function workflowIdForToolCall(call: AssistantToolResult): string | null {
  return (
    optionalStringValue(call.output.workflow_id) ??
    optionalStringValue(recordValue(call.output.workflow).workflow_id) ??
    optionalStringValue(call.arguments.workflow_id)
  );
}

function workflowIdForEvidence(
  evidence: Evidence,
  toolCalls: AssistantToolResult[],
): string | null {
  for (const call of toolCalls) {
    const evidenceIds = toolEvidence(call).map((item) => item.evidence_id);
    if (evidenceIds.includes(evidence.evidence_id)) return workflowIdForToolCall(call);
  }
  return null;
}

function evidenceForSummary(
  item: AssistantEvidenceSummary,
  toolCalls: AssistantToolResult[],
): Evidence | null {
  const evidenceId = optionalStringValue(item.evidence_id);
  const allEvidence = toolCalls.flatMap(toolEvidence);
  if (evidenceId) {
    const exact = allEvidence.find((evidence) => evidence.evidence_id === evidenceId);
    if (exact) return exact;
  }
  return (
    allEvidence.find((evidence) => evidence.source_id === item.source_id) ??
    (evidenceId
      ? {
          evidence_id: evidenceId,
          source_id: item.source_id,
          source_type: item.source_type ?? "unknown",
          claim: item.claim,
          trust_level: item.trust_level,
          confidence: item.confidence ?? null,
          locator: item.locator ?? {},
        }
      : null)
  );
}

function validationIssuesForToolCall(call: AssistantToolResult): Record<string, unknown>[] {
  const direct = validationIssuesValue(call.output.validation_report);
  if (direct.length) return direct;
  const validation = recordValue(call.output.validation);
  return validationIssuesValue(validation.validation_report);
}

function validationIssuesValue(value: unknown): Record<string, unknown>[] {
  const report = recordValue(value);
  const issues = report.issues;
  return Array.isArray(issues) ? issues.map(recordValue).filter((issue) => Object.keys(issue).length) : [];
}

function issueKindsForResponse(response: AssistantResponse): string[] {
  return uniqueStrings(
    response.tool_calls.flatMap((call) =>
      validationIssuesForToolCall(call).map((issue) => optionalStringValue(issue.kind)),
    ),
  );
}

function evidenceIdsForResponse(response: AssistantResponse): string[] {
  return uniqueStrings([
    ...response.evidence_summary.map((item) => optionalStringValue(item.evidence_id)),
    ...response.tool_calls
      .flatMap(toolEvidence)
      .map((item) => optionalStringValue(item.evidence_id)),
  ]);
}

function unresolvedFindingsForResponse(response: AssistantResponse): AssistantFinding[] {
  return response.findings.filter(findingNeedsReview);
}

function findingNeedsReview(finding: AssistantFinding): boolean {
  return (
    finding.severity === "warning" ||
    finding.severity === "action_required" ||
    finding.severity === "error"
  );
}

function uniqueStrings(values: (string | null)[]): string[] {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value))));
}

export function assistantEvidenceMatchExplanation(
  item: AssistantEvidenceSummary,
): AssistantEvidenceMatchExplanation | null {
  const explanation = recordValue(item.match_explanation);
  const supportStatus = matchSupportStatusValue(explanation.support_status);
  if (!supportStatus) return null;
  return {
    aspectLabels: stringArrayValue(explanation.aspect_labels).slice(0, 3),
    bucketLabels: stringArrayValue(explanation.bucket_labels).slice(0, 3),
    conceptLabels: stringArrayValue(explanation.concept_labels).slice(0, 3),
    provenanceCount: numberValue(explanation.provenance_count) ?? 0,
    rankingSignalCount: numberValue(explanation.ranking_signal_count) ?? 0,
    supportStatus,
    topScoreDriver: optionalStringValue(explanation.top_score_driver),
  };
}

function matchSupportStatusValue(value: unknown): "strong" | "partial" | "weak" | null {
  return value === "strong" || value === "partial" || value === "weak" ? value : null;
}

export function matchSupportBadgeVariant(
  status: "strong" | "partial" | "weak",
): AssistantBadgeVariant {
  if (status === "strong") return "success";
  if (status === "partial") return "warning";
  return "destructive";
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

export function stringArrayValue(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string" && Boolean(item.trim()))
    : [];
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function toolEvidence(call: AssistantToolResult): Evidence[] {
  const evidence = call.output.evidence;
  if (Array.isArray(evidence)) return evidence as Evidence[];
  const retrieval = call.output.retrieval;
  if (retrieval && typeof retrieval === "object" && !Array.isArray(retrieval)) {
    const nested = (retrieval as Record<string, unknown>).evidence;
    if (Array.isArray(nested)) return nested as Evidence[];
  }
  return [];
}

export function toolEvidenceBuckets(call: AssistantToolResult): RetrievalEvidenceBucket[] {
  const direct = call.output.evidence_buckets;
  if (Array.isArray(direct)) return direct as RetrievalEvidenceBucket[];
  const retrieval = call.output.retrieval;
  if (retrieval && typeof retrieval === "object" && !Array.isArray(retrieval)) {
    const nested = (retrieval as Record<string, unknown>).evidence_buckets;
    if (Array.isArray(nested)) return nested as RetrievalEvidenceBucket[];
  }
  return [];
}

export function toolStandardSearchPlan(call: AssistantToolResult): RetrievalStandardSearchPlan | null {
  const direct = standardSearchPlanValue(call.output.standard_search_plan);
  if (direct) return direct;
  const handoff = recordValue(call.output.handoff_context);
  const handoffPlan = standardSearchPlanValue(handoff.standard_search_plan);
  if (handoffPlan) return handoffPlan;
  const retrieval = recordValue(call.output.retrieval);
  const retrievalPlan = standardSearchPlanValue(retrieval.standard_search_plan);
  if (retrievalPlan) return retrievalPlan;
  const retrievalHandoff = recordValue(retrieval.handoff_context);
  return standardSearchPlanValue(retrievalHandoff.standard_search_plan);
}

export function toolSearchHints(call: AssistantToolResult): AssistantSearchHint[] {
  const direct = searchHintsValue(call.output.search_hints);
  if (direct.length) return direct;
  const queryAnalysis = recordValue(call.output.query_analysis);
  const queryAnalysisHints = searchHintsValue(queryAnalysis.search_hints);
  if (queryAnalysisHints.length) return queryAnalysisHints;
  const handoff = recordValue(call.output.handoff_context);
  const handoffAnalysis = recordValue(handoff.query_analysis);
  const handoffHints = searchHintsValue(handoffAnalysis.search_hints);
  if (handoffHints.length) return handoffHints;
  const retrieval = recordValue(call.output.retrieval);
  const retrievalAnalysis = recordValue(retrieval.query_analysis);
  const retrievalAnalysisHints = searchHintsValue(retrievalAnalysis.search_hints);
  if (retrievalAnalysisHints.length) return retrievalAnalysisHints;
  const retrievalHandoff = recordValue(retrieval.handoff_context);
  const retrievalHandoffAnalysis = recordValue(retrievalHandoff.query_analysis);
  return searchHintsValue(retrievalHandoffAnalysis.search_hints);
}

export function toolDiversitySummary(call: AssistantToolResult): RetrievalDiversitySummary | null {
  const direct = diversitySummaryValue(call.output.diversity);
  if (direct) return direct;
  const handoff = recordValue(call.output.handoff_context);
  const handoffDiversity = diversitySummaryValue(handoff.diversity);
  if (handoffDiversity) return handoffDiversity;
  const retrieval = recordValue(call.output.retrieval);
  const retrievalDiversity = diversitySummaryValue(retrieval.diversity);
  if (retrievalDiversity) return retrievalDiversity;
  const retrievalHandoff = recordValue(retrieval.handoff_context);
  return diversitySummaryValue(retrievalHandoff.diversity);
}

function diversitySummaryValue(value: unknown): RetrievalDiversitySummary | null {
  const record = recordValue(value);
  const candidateSourceCount = numberValue(record.candidate_source_count);
  const selectedSourceCount = numberValue(record.selected_source_count);
  const duplicateSelectedSourceCount = numberValue(record.duplicate_selected_source_count);
  if (
    candidateSourceCount === null ||
    selectedSourceCount === null ||
    duplicateSelectedSourceCount === null
  ) {
    return null;
  }
  return {
    enabled: Boolean(record.enabled),
    selection_mode: optionalStringValue(record.selection_mode) ?? "score_order",
    lambda_value: numberValue(record.lambda_value) ?? numberValue(record.lambda),
    candidate_source_count: candidateSourceCount,
    selected_source_count: selectedSourceCount,
    duplicate_selected_source_count: duplicateSelectedSourceCount,
    selected_hits: diversitySelectionValues(record.selected_hits),
  };
}

function diversitySelectionValues(value: unknown): RetrievalDiversitySelection[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      evidence_id: optionalStringValue(item.evidence_id) ?? "",
      source_id: optionalStringValue(item.source_id) ?? "",
      selected_rank: numberValue(item.selected_rank) ?? 0,
      original_rank: numberValue(item.original_rank) ?? 0,
      relevance_score: numberValue(item.relevance_score) ?? 0,
      redundancy_score: numberValue(item.redundancy_score) ?? 0,
      selection_score: numberValue(item.selection_score) ?? 0,
      reason: optionalStringValue(item.reason) ?? "Selected retrieval evidence.",
    }))
    .filter((item) => item.evidence_id && item.source_id);
}

function searchHintsValue(value: unknown): AssistantSearchHint[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      metadata: recordValue(item.metadata),
      query: optionalStringValue(item.query) ?? "",
      rationale: optionalStringValue(item.rationale) ?? "Generated by retrieval analysis.",
      target: optionalStringValue(item.target) ?? "",
      url: optionalStringValue(item.url),
      warnings: stringArrayValue(item.warnings),
    }))
    .filter((item) => item.target && item.query);
}

export function arrayCount(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}

function standardSearchPlanValue(value: unknown): RetrievalStandardSearchPlan | null {
  const record = recordValue(value);
  const planId = optionalStringValue(record.plan_id);
  const summary = optionalStringValue(record.summary);
  const primaryRoute = optionalStringValue(record.primary_route);
  const rawSteps = Array.isArray(record.steps) ? record.steps : [];
  const steps = rawSteps
    .map(standardSearchStepValue)
    .filter((step): step is RetrievalStandardSearchStep => step !== null);
  if (!planId || !summary || !primaryRoute || !steps.length) {
    return null;
  }
  return {
    plan_id: planId,
    summary,
    primary_route: primaryRoute,
    steps,
    missing_routes: stringArrayValue(record.missing_routes),
    governance_notes: stringArrayValue(record.governance_notes),
    metadata: recordValue(record.metadata),
  };
}

function standardSearchStepValue(value: unknown): RetrievalStandardSearchStep | null {
  const record = recordValue(value);
  const stepId = optionalStringValue(record.step_id);
  const label = optionalStringValue(record.label);
  const standardSystem = optionalStringValue(record.standard_system);
  const routeType = optionalStringValue(record.route_type);
  const query = optionalStringValue(record.query);
  const rationale = optionalStringValue(record.rationale);
  const priority = numberValue(record.priority);
  if (
    !stepId ||
    !label ||
    !standardSystem ||
    !routeType ||
    !query ||
    !rationale ||
    priority === null
  ) {
    return null;
  }
  return {
    step_id: stepId,
    label,
    standard_system: standardSystem,
    route_type: routeType,
    query,
    rationale,
    priority,
    suggested_filters: stringRecordValue(record.suggested_filters),
    governance_notes: stringArrayValue(record.governance_notes),
    metadata: recordValue(record.metadata),
  };
}

function stringRecordValue(value: unknown): Record<string, string> {
  const record = recordValue(value);
  return Object.fromEntries(
    Object.entries(record).filter(
      (entry): entry is [string, string] => typeof entry[1] === "string",
    ),
  );
}

export function badgeVariant(status: AssistantToolResult["status"]) {
  if (status === "completed") return "success";
  if (status === "failed") return "destructive";
  if (status === "requires_approval") return "warning";
  return "muted";
}

export function findingBadgeVariant(severity: AssistantFinding["severity"]) {
  if (severity === "error") return "destructive";
  if (severity === "warning" || severity === "action_required") return "warning";
  return "success";
}

export function assistantEvidenceBucketVariant(bucket: RetrievalEvidenceBucket) {
  if (bucket.hit_count > 0) return "success";
  return bucket.required ? "warning" : "muted";
}
