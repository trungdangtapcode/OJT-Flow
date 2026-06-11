import type {
  RetrievalPlanRiskSignal,
  RetrievalPlanTaskSummary,
} from "../../../types";
import type { SearchPlanCoverageStack } from "./retrieval-query-analysis-types";
import {
  booleanValue,
  numberValue,
  optionalStringValue,
  recordValue,
  stringArrayValue,
  stringValue,
} from "./retrieval-query-analysis-coercion";

export function planTaskSummaryValue(value: unknown): RetrievalPlanTaskSummary | null {
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

export function planCoverageSummaryValue(value: unknown): SearchPlanCoverageStack | null {
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

export function planRiskSignalsValue(value: unknown): RetrievalPlanRiskSignal[] {
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
