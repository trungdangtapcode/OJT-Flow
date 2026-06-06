import { humanize } from "../../../lib/utils";
import type { RetrievalSearchPayload, RuntimeRetrievalRulePack } from "../../../types";
import { searchRunRemediationSummary, type SearchRunSummaryView } from "./search-run-presentation";

export type RetrievalComparisonDiagnosis = {
  code: string;
  message: string;
  severity: "success" | "warning" | "muted";
};

export type RetrievalComparisonRecommendedAction = {
  action: string;
  priority: number;
  reason: string;
  severity: "success" | "warning" | "destructive" | "muted";
  source: string;
};

export type RetrievalComparisonRecommendedActionSummary = {
  action_count: number;
  badge_variant: "success" | "warning" | "destructive";
  highest_priority: number | null;
  highest_severity: "success" | "warning" | "destructive";
  source_count: number;
  source_counts: Record<string, number>;
  sources: string[];
};

export type RetrievalComparisonOperatorSummary = {
  bullets: string[];
  headline: string;
  reviewFocus: string[];
  status: "stable" | "review" | "improved";
};

export type RetrievalComparisonDiagnosticInput = {
  addedEvidenceIds: string[];
  conceptGroundingComparison: {
    added: unknown[];
    removed: unknown[];
  };
  coverageComparison: {
    added: unknown[];
    improved: unknown[];
    regressed: unknown[];
  };
  facetComparisons: Array<{
    activeCount: number;
    addedValues: string[];
    baselineCount: number;
    field: string;
    label: string;
    removedValues: string[];
    retainedValues: string[];
  }>;
  qualityScoreDelta: number | null;
  qualitySignalComparison: {
    added: unknown[];
    removed: unknown[];
  };
  qualitySummaryChanged: boolean;
  queryAspectComparison: {
    added: unknown[];
    removed: unknown[];
  };
  queryProfileChanged: boolean;
  rankChanges: unknown[];
  removedEvidenceIds: string[];
  rulePackChanged: boolean;
  sourceDiversityComparison: {
    candidateSourceDelta: number;
    duplicateSelectedSourceDelta: number;
    lambdaChanged: boolean;
    selectedSourceDelta: number;
    selectionModeChanged: boolean;
    sourceOverlapRatio: number;
  };
  topSourceChanged: boolean;
};

export type RetrievalComparisonRecommendationInput = RetrievalComparisonDiagnosticInput & {
  activeSummary: {
    qualitySummary: {
      status: string;
      top_action?: string | null;
    } | null;
  };
  metrics: {
    churnRate: number;
    overlapRatio: number;
  };
  qualityWarningDelta: number;
};

export type RetrievalComparisonOperatorSummaryInput =
  RetrievalComparisonRecommendationInput & {
    diagnosis: RetrievalComparisonDiagnosis[];
    qualityScoreDelta: number | null;
  };

export type RetrievalComparisonJudgmentInput = {
  evidenceId: string;
  judgedAt?: string;
  query?: string;
  rating?: number;
  runId?: string;
  value?: string;
};

export type RetrievalComparisonReportInput = RetrievalComparisonRecommendationInput & {
  activePayload: RetrievalSearchPayload;
  activeQuery: string;
  activeRunId: string;
  activeSubmittedAt: string;
  activeSummary: SearchRunSummaryView & {
    queryProfile?: unknown;
    serverSignature?: string | null;
  };
  baselinePayload: RetrievalSearchPayload;
  baselineQuery: string;
  baselineRunId: string;
  baselineSubmittedAt: string;
  baselineSummary: SearchRunSummaryView & {
    queryProfile?: unknown;
    serverSignature?: string | null;
  };
  candidateDelta: number;
  conceptGroundingComparison: {
    added: unknown[];
    removed: unknown[];
    retained: unknown[];
  };
  coverageComparison: {
    added: unknown[];
    improved: unknown[];
    regressed: unknown[];
    removed: unknown[];
    retained: unknown[];
  };
  diagnosis: RetrievalComparisonDiagnosis[];
  facetComparisons: Array<{
    activeCount: number;
    addedValues: string[];
    baselineCount: number;
    field: string;
    label: string;
    removedValues: string[];
    retainedValues: string[];
  }>;
  hitDelta: number;
  metrics: {
    churnRate: number;
    overlapRatio: number;
    [key: string]: unknown;
  };
  queryAspectComparison: {
    added: unknown[];
    removed: unknown[];
    retained: unknown[];
  };
  qualityScoreDelta: number | null;
  qualitySignalComparison: {
    added: unknown[];
    removed: unknown[];
    retained: unknown[];
  };
  rankChanges: unknown[];
  retainedEvidenceIds: string[];
  rulePackChanges: Array<{
    active?: RuntimeRetrievalRulePack;
    baseline?: RuntimeRetrievalRulePack;
    name: string;
    status: string;
  }>;
  sourceDiversityComparison: RetrievalComparisonRecommendationInput["sourceDiversityComparison"] & {
    active: {
      candidateSourceCount: number;
      duplicateSelectedSourceCount: number;
      enabled: boolean;
      lambda: number | null;
      selectedSourceCount: number;
      selectionMode: string;
    };
    activeSelectedSourceIds: string[];
    addedSourceIds: string[];
    baseline: {
      candidateSourceCount: number;
      duplicateSelectedSourceCount: number;
      enabled: boolean;
      lambda: number | null;
      selectedSourceCount: number;
      selectionMode: string;
    };
    baselineSelectedSourceIds: string[];
    removedSourceIds: string[];
    retainedSourceIds: string[];
    sourceOverlapRatio: number;
  };
  topSourceAfter: string | null;
  topSourceBefore: string | null;
  warningDelta: number;
};

export function comparisonDiagnosisFromComparison(
  comparison: RetrievalComparisonDiagnosticInput,
): RetrievalComparisonDiagnosis[] {
  const diagnosis: RetrievalComparisonDiagnosis[] = [];
  if (comparison.queryProfileChanged) {
    diagnosis.push({
      code: "query_profile_changed",
      message:
        "Query profile, route, retrieval mode, or complexity changed between runs.",
      severity: "warning",
    });
  }
  if (comparison.rulePackChanged) {
    diagnosis.push({
      code: "rule_pack_changed",
      message: "Retrieval rule-pack fingerprints changed between runs.",
      severity: "warning",
    });
  }
  if (
    comparison.queryAspectComparison.added.length ||
    comparison.queryAspectComparison.removed.length
  ) {
    diagnosis.push({
      code: "query_aspect_plan_changed",
      message: "Search aspect coverage plan changed between runs.",
      severity: "warning",
    });
  }
  if (
    comparison.conceptGroundingComparison.added.length ||
    comparison.conceptGroundingComparison.removed.length
  ) {
    diagnosis.push({
      code: "concept_grounding_changed",
      message: "Controlled medical concept grounding changed between runs.",
      severity: "warning",
    });
  }
  if (comparison.coverageComparison.regressed.length || comparison.coverageComparison.added.length) {
    diagnosis.push({
      code: "coverage_diagnostics_changed",
      message: "Coverage diagnostics changed between runs.",
      severity: "warning",
    });
  } else if (comparison.coverageComparison.improved.length) {
    diagnosis.push({
      code: "coverage_improved",
      message: "Coverage diagnostics improved between runs.",
      severity: "success",
    });
  }
  if (
    comparison.qualitySignalComparison.added.length ||
    comparison.qualitySignalComparison.removed.length
  ) {
    diagnosis.push({
      code: "quality_signal_changed",
      message: "Package-level quality signals were added or removed.",
      severity: "warning",
    });
  }
  if (comparison.qualitySummaryChanged) {
    diagnosis.push({
      code: "quality_summary_changed",
      message: "Readiness status, score, or top action changed between runs.",
      severity:
        comparison.qualityScoreDelta !== null && comparison.qualityScoreDelta > 0
          ? "success"
          : "warning",
    });
  }
  if (
    comparison.facetComparisons.some(
      (facet) => facet.addedValues.length || facet.removedValues.length,
    )
  ) {
    diagnosis.push({
      code: "facet_coverage_changed",
      message:
        "Selected-hit source type, clinical domain, standard, or trust coverage changed.",
      severity: "warning",
    });
  }
  if (comparison.topSourceChanged) {
    diagnosis.push({
      code: "top_source_changed",
      message: "The highest-ranked source changed between runs.",
      severity: "warning",
    });
  }
  if (
    comparison.sourceDiversityComparison.selectionModeChanged ||
    comparison.sourceDiversityComparison.lambdaChanged
  ) {
    diagnosis.push({
      code: "source_diversity_policy_changed",
      message: "Source-diversity selection mode or lambda changed between runs.",
      severity: "warning",
    });
  }
  if (comparison.sourceDiversityComparison.duplicateSelectedSourceDelta > 0) {
    diagnosis.push({
      code: "source_diversity_regressed",
      message:
        "The active run selected more duplicate evidence from already selected sources.",
      severity: "warning",
    });
  } else if (
    comparison.sourceDiversityComparison.selectedSourceDelta > 0 ||
    comparison.sourceDiversityComparison.duplicateSelectedSourceDelta < 0
  ) {
    diagnosis.push({
      code: "source_diversity_improved",
      message:
        "The active run improved selected-source coverage or reduced duplicate-source evidence.",
      severity: "success",
    });
  }
  if (comparison.rankChanges.length) {
    diagnosis.push({
      code: "rank_movement",
      message: "Retained evidence moved position in the ranked result set.",
      severity: "warning",
    });
  }
  if (comparison.addedEvidenceIds.length || comparison.removedEvidenceIds.length) {
    diagnosis.push({
      code: "evidence_set_changed",
      message: "The retrieved evidence set added or removed source chunks.",
      severity: "warning",
    });
  }
  if (!diagnosis.length) {
    diagnosis.push({
      code: "comparison_stable",
      message:
        "Comparison is stable across query profile, concept grounding, search aspects, rules, quality, facets, evidence, and ranks.",
      severity: "success",
    });
  }
  return diagnosis;
}

export function comparisonReportRecommendedActions(
  comparison: RetrievalComparisonRecommendationInput,
  judgments: RetrievalComparisonJudgmentInput[],
): RetrievalComparisonRecommendedAction[] {
  const actions: RetrievalComparisonRecommendedAction[] = [];
  const activeTopAction = comparison.activeSummary.qualitySummary?.top_action;
  if (activeTopAction) {
    actions.push({
      action: activeTopAction,
      priority: comparison.activeSummary.qualitySummary?.status === "blocked" ? 1 : 2,
      reason: "Active retrieval package readiness policy selected this top action.",
      severity:
        comparison.activeSummary.qualitySummary?.status === "blocked"
          ? "destructive"
          : "warning",
      source: "quality_summary.top_action",
    });
  }
  if (
    comparison.coverageComparison.regressed.length ||
    comparison.coverageComparison.added.length
  ) {
    actions.push({
      action: "Review coverage diagnostics and apply supported standard/aspect filters before accepting this run.",
      priority: 1,
      reason: "Coverage diagnostics were added or regressed between baseline and active runs.",
      severity: "warning",
      source: "coverage",
    });
  }
  if (comparison.queryProfileChanged) {
    actions.push({
      action: "Confirm the active query profile, route, and retrieval mode match the intended search task.",
      priority: 3,
      reason: "Adaptive query-profile guidance changed between runs.",
      severity: "warning",
      source: "query_profile",
    });
  }
  if (comparison.rulePackChanged) {
    actions.push({
      action: "Record the active rule-pack fingerprints with any relevance-tuning decision.",
      priority: 3,
      reason: "Rule-pack data changed, so ranking movement may not be caused only by query edits.",
      severity: "warning",
      source: "rule_packs",
    });
  }
  if (comparison.qualitySignalComparison.added.length) {
    actions.push({
      action: "Inspect newly added quality signals before using the active evidence package downstream.",
      priority: 1,
      reason: "The active run added package-level quality signals.",
      severity: "warning",
      source: "quality_signals",
    });
  }
  if (comparison.metrics.churnRate > 0.5 || comparison.topSourceChanged) {
    actions.push({
      action: "Compare added, removed, and retained evidence before treating the active run as equivalent to baseline.",
      priority: 2,
      reason: "Evidence churn or top-source movement is high enough to affect review conclusions.",
      severity: "warning",
      source: "evidence",
    });
  }
  if (comparison.sourceDiversityComparison.duplicateSelectedSourceDelta > 0) {
    actions.push({
      action: "Review whether active results over-concentrate evidence from the same source family before accepting the tuning change.",
      priority: 2,
      reason: "The active run selected more duplicate-source evidence than the baseline.",
      severity: "warning",
      source: "source_diversity",
    });
  }
  if (
    comparison.sourceDiversityComparison.selectionModeChanged ||
    comparison.sourceDiversityComparison.lambdaChanged
  ) {
    actions.push({
      action: "Document source-diversity policy changes with this comparison result.",
      priority: 3,
      reason: "Selection mode or lambda changed, so source spread is not directly comparable without configuration context.",
      severity: "warning",
      source: "source_diversity",
    });
  }
  if (!judgments.length) {
    actions.push({
      action: "Add explicit relevance judgments for top hits before using this comparison as an evaluation record.",
      priority: 4,
      reason: "The copied comparison does not include any operator judgments.",
      severity: "muted",
      source: "judgments",
    });
  }
  if (!actions.length) {
    actions.push({
      action: "Keep the active retrieval configuration; no comparison follow-up was detected.",
      priority: 5,
      reason: "Comparison diagnostics are stable and no missing review signal was detected.",
      severity: "success",
      source: "comparison_stable",
    });
  }
  return actions.sort(
    (left, right) =>
      left.priority - right.priority || left.source.localeCompare(right.source),
  );
}

export function comparisonReportFromComparison(
  comparison: RetrievalComparisonReportInput,
  judgments: RetrievalComparisonJudgmentInput[],
  recommendedActions: RetrievalComparisonRecommendedAction[] = comparisonReportRecommendedActions(
    comparison,
    judgments,
  ),
) {
  return {
    report_type: "retrieval_run_comparison",
    version: 1,
    generated_at: new Date().toISOString(),
    summary: comparisonReportSummary(comparison, judgments),
    operator_summary: comparisonOperatorSummary(comparison, recommendedActions),
    remediation: {
      active:
        comparison.activeSummary.remediationSummary ??
        searchRunRemediationSummary(comparison.activeSummary),
      baseline:
        comparison.baselineSummary.remediationSummary ??
        searchRunRemediationSummary(comparison.baselineSummary),
    },
    recommended_action_summary: comparisonRecommendedActionSummary(recommendedActions),
    recommended_actions: recommendedActions,
    active: {
      query: comparison.activeQuery,
      run_id: comparison.activeRunId,
      search_signature: comparison.activeSummary.serverSignature,
      submitted_at: comparison.activeSubmittedAt,
      payload: comparison.activePayload,
      remediation_summary:
        comparison.activeSummary.remediationSummary ??
        searchRunRemediationSummary(comparison.activeSummary),
      summary: comparison.activeSummary,
    },
    baseline: {
      query: comparison.baselineQuery,
      run_id: comparison.baselineRunId,
      search_signature: comparison.baselineSummary.serverSignature,
      submitted_at: comparison.baselineSubmittedAt,
      payload: comparison.baselinePayload,
      remediation_summary:
        comparison.baselineSummary.remediationSummary ??
        searchRunRemediationSummary(comparison.baselineSummary),
      summary: comparison.baselineSummary,
    },
    deltas: {
      candidates: comparison.candidateDelta,
      hits: comparison.hitDelta,
      quality_score: comparison.qualityScoreDelta,
      quality_warnings: comparison.qualityWarningDelta,
      source_diversity: {
        candidate_sources: comparison.sourceDiversityComparison.candidateSourceDelta,
        duplicate_selected_sources:
          comparison.sourceDiversityComparison.duplicateSelectedSourceDelta,
        selected_sources: comparison.sourceDiversityComparison.selectedSourceDelta,
      },
      warnings: comparison.warningDelta,
    },
    diagnosis: comparison.diagnosis,
    metrics: comparison.metrics,
    coverage: {
      added: comparison.coverageComparison.added,
      improved: comparison.coverageComparison.improved,
      regressed: comparison.coverageComparison.regressed,
      removed: comparison.coverageComparison.removed,
      retained: comparison.coverageComparison.retained,
    },
    query_aspects: {
      added: comparison.queryAspectComparison.added,
      removed: comparison.queryAspectComparison.removed,
      retained: comparison.queryAspectComparison.retained,
    },
    concept_grounding: {
      added: comparison.conceptGroundingComparison.added,
      removed: comparison.conceptGroundingComparison.removed,
      retained: comparison.conceptGroundingComparison.retained,
    },
    quality_signals: {
      added: comparison.qualitySignalComparison.added,
      removed: comparison.qualitySignalComparison.removed,
      retained: comparison.qualitySignalComparison.retained,
    },
    facets: comparison.facetComparisons.map((facet) => ({
      field: facet.field,
      label: facet.label,
      active_count: facet.activeCount,
      baseline_count: facet.baselineCount,
      added_values: facet.addedValues,
      removed_values: facet.removedValues,
      retained_values: facet.retainedValues,
    })),
    judgments: judgments.map((judgment) => ({
      doc_id: judgment.evidenceId,
      evidence_id: judgment.evidenceId,
      judged_at: judgment.judgedAt,
      query: judgment.query,
      rating: judgment.rating,
      run_id: judgment.runId,
      value: judgment.value,
    })),
    evidence: {
      added_ids: comparison.addedEvidenceIds,
      removed_ids: comparison.removedEvidenceIds,
      retained_ids: comparison.retainedEvidenceIds,
      rank_changes: comparison.rankChanges,
    },
    top_source: {
      before: comparison.topSourceBefore,
      after: comparison.topSourceAfter,
      changed: comparison.topSourceChanged,
    },
    source_diversity: {
      active: {
        candidate_source_count:
          comparison.sourceDiversityComparison.active.candidateSourceCount,
        duplicate_selected_source_count:
          comparison.sourceDiversityComparison.active.duplicateSelectedSourceCount,
        enabled: comparison.sourceDiversityComparison.active.enabled,
        lambda: comparison.sourceDiversityComparison.active.lambda,
        selected_source_count:
          comparison.sourceDiversityComparison.active.selectedSourceCount,
        selection_mode: comparison.sourceDiversityComparison.active.selectionMode,
        selected_source_ids:
          comparison.sourceDiversityComparison.activeSelectedSourceIds,
      },
      baseline: {
        candidate_source_count:
          comparison.sourceDiversityComparison.baseline.candidateSourceCount,
        duplicate_selected_source_count:
          comparison.sourceDiversityComparison.baseline.duplicateSelectedSourceCount,
        enabled: comparison.sourceDiversityComparison.baseline.enabled,
        lambda: comparison.sourceDiversityComparison.baseline.lambda,
        selected_source_count:
          comparison.sourceDiversityComparison.baseline.selectedSourceCount,
        selection_mode: comparison.sourceDiversityComparison.baseline.selectionMode,
        selected_source_ids:
          comparison.sourceDiversityComparison.baselineSelectedSourceIds,
      },
      added_source_ids: comparison.sourceDiversityComparison.addedSourceIds,
      removed_source_ids: comparison.sourceDiversityComparison.removedSourceIds,
      retained_source_ids: comparison.sourceDiversityComparison.retainedSourceIds,
      source_overlap_ratio: comparison.sourceDiversityComparison.sourceOverlapRatio,
      selection_mode_changed:
        comparison.sourceDiversityComparison.selectionModeChanged,
      lambda_changed: comparison.sourceDiversityComparison.lambdaChanged,
    },
    query_profiles: {
      before: comparison.baselineSummary.queryProfile,
      after: comparison.activeSummary.queryProfile,
      changed: comparison.queryProfileChanged,
    },
    rule_packs: {
      changed: comparison.rulePackChanged,
      changes: comparison.rulePackChanges.map((change) => ({
        name: change.name,
        status: change.status,
        before: change.baseline ?? null,
        after: change.active ?? null,
      })),
    },
  };
}

export function comparisonRecommendedActionSummary(
  actions: RetrievalComparisonRecommendedAction[],
): RetrievalComparisonRecommendedActionSummary {
  const sources = new Set(actions.map((action) => action.source));
  const sourceCounts = actions.reduce<Record<string, number>>((counts, action) => {
    counts[action.source] = (counts[action.source] ?? 0) + 1;
    return counts;
  }, {});
  const highestPriority = Math.min(...actions.map((action) => action.priority));
  const hasDestructive = actions.some((action) => action.severity === "destructive");
  const hasWarning = actions.some((action) => action.severity === "warning");
  return {
    action_count: actions.length,
    badge_variant: hasDestructive ? "destructive" : hasWarning ? "warning" : "success",
    highest_priority: Number.isFinite(highestPriority) ? highestPriority : null,
    highest_severity: hasDestructive ? "destructive" : hasWarning ? "warning" : "success",
    source_count: sources.size,
    source_counts: sourceCounts,
    sources: Array.from(sources).sort(),
  };
}

export function comparisonOperatorSummary(
  comparison: RetrievalComparisonOperatorSummaryInput,
  recommendedActions: RetrievalComparisonRecommendedAction[],
): RetrievalComparisonOperatorSummary {
  const warnings = comparison.diagnosis.filter(
    (item) => item.severity === "warning",
  );
  const improvements = comparison.diagnosis.filter(
    (item) => item.severity === "success" && item.code !== "comparison_stable",
  );
  const diversity = comparison.sourceDiversityComparison;
  const status: RetrievalComparisonOperatorSummary["status"] = warnings.length
    ? "review"
    : improvements.length
      ? "improved"
      : "stable";
  const headline =
    status === "review"
      ? `Review ${formatCount(warnings.length, "change driver")} before accepting this retrieval tuning run.`
      : status === "improved"
        ? "Active run improved one or more retrieval readiness signals without warning drivers."
        : "Active run is stable against the selected baseline.";
  const topAction =
    recommendedActions.find((action) => action.severity !== "success") ??
    recommendedActions[0] ??
    null;
  const sourceSpread =
    diversity.selectedSourceDelta === 0 &&
    diversity.duplicateSelectedSourceDelta === 0
      ? "Source spread is unchanged."
      : `Source spread ${formatSignedDelta(
          diversity.selectedSourceDelta,
        )}; duplicate-source evidence ${formatSignedDelta(
          diversity.duplicateSelectedSourceDelta,
        )}.`;
  const bullets = [
    `Evidence overlap ${formatPercent(comparison.metrics.overlapRatio)}; churn ${formatPercent(comparison.metrics.churnRate)}.`,
    `Quality score delta ${
      comparison.qualityScoreDelta === null
        ? "n/a"
        : formatSignedDelta(comparison.qualityScoreDelta)
    }; quality warnings ${formatSignedDelta(comparison.qualityWarningDelta)}.`,
    sourceSpread,
    topAction
      ? `Next action: ${topAction.action}`
      : "No follow-up action detected.",
  ];
  const reviewFocus = uniqueValues([
    ...warnings.slice(0, 4).map((item) => humanize(item.code)),
    ...(diversity.duplicateSelectedSourceDelta > 0 ? ["source concentration"] : []),
    ...(comparison.metrics.churnRate > 0.5 ? ["evidence churn"] : []),
    ...(comparison.rankChanges.length ? ["rank movement"] : []),
    ...(comparison.qualitySummaryChanged ? ["quality readiness"] : []),
  ]);

  return {
    bullets,
    headline,
    reviewFocus: reviewFocus.length ? reviewFocus : ["no immediate review focus"],
    status,
  };
}

function comparisonReportSummary(
  comparison: RetrievalComparisonReportInput,
  judgments: RetrievalComparisonJudgmentInput[],
) {
  return {
    active_query: comparison.activeQuery,
    baseline_query: comparison.baselineQuery,
    status: comparison.diagnosis.some((item) => item.severity === "warning")
      ? "changed"
      : "stable",
    top_diagnosis: comparison.diagnosis[0] ?? null,
    quality: {
      before_status: comparison.baselineSummary.qualitySummary?.status ?? null,
      after_status: comparison.activeSummary.qualitySummary?.status ?? null,
      before_score: comparison.baselineSummary.qualitySummary?.score ?? null,
      after_score: comparison.activeSummary.qualitySummary?.score ?? null,
      score_delta: comparison.qualityScoreDelta,
      before_top_action: comparison.baselineSummary.qualitySummary?.top_action ?? null,
      after_top_action: comparison.activeSummary.qualitySummary?.top_action ?? null,
      changed: comparison.qualitySummaryChanged,
    },
    evidence: {
      added_count: comparison.addedEvidenceIds.length,
      removed_count: comparison.removedEvidenceIds.length,
      retained_count: comparison.retainedEvidenceIds.length,
      rank_change_count: comparison.rankChanges.length,
      top_source_changed: comparison.topSourceChanged,
    },
    top_source: {
      before: comparison.topSourceBefore,
      after: comparison.topSourceAfter,
      changed: comparison.topSourceChanged,
    },
    retrieval: {
      hit_delta: comparison.hitDelta,
      candidate_delta: comparison.candidateDelta,
      warning_delta: comparison.warningDelta,
      quality_warning_delta: comparison.qualityWarningDelta,
      overlap_ratio: comparison.metrics.overlapRatio,
      churn_ratio: comparison.metrics.churnRate,
      source_diversity: {
        selected_source_delta:
          comparison.sourceDiversityComparison.selectedSourceDelta,
        duplicate_selected_source_delta:
          comparison.sourceDiversityComparison.duplicateSelectedSourceDelta,
        source_overlap_ratio:
          comparison.sourceDiversityComparison.sourceOverlapRatio,
      },
    },
    changed_dimensions: comparison.diagnosis
      .filter((item) => item.severity !== "success")
      .map((item) => item.code),
    judgment_count: judgments.length,
  };
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatSignedDelta(delta: number): string {
  return delta > 0 ? `+${delta}` : String(delta);
}

function uniqueValues(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value))));
}
