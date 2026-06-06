import { humanize } from "../../../lib/utils";
import type {
  RetrievalCoverage,
  RetrievalHit,
  RetrievalPackage,
  RetrievalQualitySignal,
  RetrievalQualitySummary,
  RetrievalRecommendedAction,
  RetrievalSearchPayload,
  RuntimeRetrievalRulePack,
} from "../../../types";
import type { DiversityStack } from "../components/source-diversity-panel";
import { queryAnalysisFromPackage } from "./retrieval-query-analysis";
import { diversityFromPackage } from "./retrieval-runtime-stack";

export type RetrievalSearchRun = {
  packageData: RetrievalPackage;
  payload: RetrievalSearchPayload;
  runId: string;
  signature: string;
  submittedAt: string;
  summary: RetrievalRunSummary;
};

export type RetrievalRunSummary = {
  candidateCount: number;
  conceptGrounding: ConceptGroundingSummary[];
  correctiveActionSummary: CorrectiveActionSummary;
  coverage: RetrievalCoverageSummary[];
  diversity: DiversityStack;
  hitCount: number;
  qualitySummary: RetrievalQualitySummary | null;
  qualityWarningCount: number;
  queryAspects: QueryAspectSummary[];
  queryProfile: QueryProfileSummary | null;
  rulePackCount: number;
  rulePackFingerprint: string;
  serverSignature: string | null;
  remediationSummary: string | null;
  topSourceId: string | null;
  warningCount: number;
};

export type CorrectiveActionSummary = {
  count: number;
  highestPriority: number | null;
  highestSeverity: string | null;
  topActionTitle: string | null;
  applyFilterCount: number;
  broadenQueryCount: number;
  actionTypeCounts: Record<string, number>;
};

export type RetrievalCoverageSummary = {
  field: string;
  label: string;
  selectedCount: number;
  status: string;
  suggestedFilter: Record<string, string>;
  value: string;
};

export type QueryAspectSummary = {
  aspectId: string;
  label: string;
  priority: number;
  question: string;
  ruleId: string;
};

export type ConceptGroundingSummary = {
  code: string | null;
  conceptId: string;
  displayName: string;
  evidenceCount: number;
  standardSystem: string;
};

export type QueryProfileSummary = {
  complexity: string;
  label: string;
  profileId: string;
  retrievalMode: string;
  route: string;
};

type ConceptMatchSignal = {
  code: string | null;
  conceptId: string;
  displayName: string;
  standardSystem: string;
};

export function retrievalRunSummary(packageData: RetrievalPackage): RetrievalRunSummary {
  const rulePacks = retrievalRulePacksFromPackage(packageData);
  return {
    candidateCount: packageData.trace.candidates_seen,
    conceptGrounding: conceptGroundingSummariesFromPackage(packageData),
    correctiveActionSummary: correctiveActionSummaryFromPackage(packageData),
    coverage: coverageSummariesFromPackage(packageData),
    diversity: diversityFromPackage(packageData),
    hitCount: packageData.hits.length,
    qualitySummary: packageData.quality_summary ?? null,
    qualityWarningCount: qualityWarningCount(packageData.quality_signals ?? []),
    queryAspects: queryAspectSummariesFromPackage(packageData),
    queryProfile: queryProfileSummaryFromPackage(packageData),
    rulePackCount: rulePacks.length,
    rulePackFingerprint: rulePacks
      .map((pack) => `${pack.name}:${rulePackFingerprint(pack)}`)
      .join("|"),
    serverSignature: serverSearchSignatureFromPackage(packageData),
    remediationSummary:
      packageData.remediation_summary ??
      optionalStringValue(packageData.handoff_context.remediation_summary) ??
      null,
    topSourceId: packageData.hits[0]?.evidence.source_id ?? null,
    warningCount: packageData.trace.warnings.length,
  };
}

export function retrievalRulePacksFromPackage(
  packageData: RetrievalPackage,
): RuntimeRetrievalRulePack[] {
  const rawPacks = packageData.handoff_context.retrieval_rule_packs;
  if (!Array.isArray(rawPacks)) return [];
  return rawPacks
    .map((rawPack) => recordValue(rawPack))
    .map((pack) => ({
      name: stringValue(pack.name, ""),
      status: rulePackStatusValue(pack.status),
      source: stringValue(pack.source, "unknown"),
      env_var: stringValue(pack.env_var, ""),
      configured: booleanValue(pack.configured),
      rule_count: numberValue(pack.rule_count) ?? 0,
      version: optionalStringValue(pack.version),
      content_hash: optionalStringValue(pack.content_hash),
      error: optionalStringValue(pack.error) ?? undefined,
    }))
    .filter((pack) => pack.name && pack.env_var);
}

export function queryProfileSummaryFromPackage(
  packageData: RetrievalPackage,
): QueryProfileSummary | null {
  const queryProfile = queryAnalysisFromPackage(packageData).queryProfile;
  if (!queryProfile) return null;
  return {
    complexity: queryProfile.complexity,
    label: queryProfile.label,
    profileId: queryProfile.profileId,
    retrievalMode: queryProfile.retrievalMode,
    route: queryProfile.route,
  };
}

export function coverageSummariesFromPackage(
  packageData: RetrievalPackage,
): RetrievalCoverageSummary[] {
  const coverage = packageData.coverage;
  const standardItems = coverage?.standard_system ?? [];
  const aspectItems = coverage?.query_aspects ?? [];
  return [
    ...standardItems.map((item) => coverageSummaryFromItem(item, "standard")),
    ...aspectItems.map((item) => coverageSummaryFromItem(item, "aspect")),
  ].sort((left, right) => coverageComparisonKey(left).localeCompare(coverageComparisonKey(right)));
}

export function queryAspectSummariesFromPackage(
  packageData: RetrievalPackage,
): QueryAspectSummary[] {
  return queryAnalysisFromPackage(packageData)
    .queryAspects.map((aspect) => ({
      aspectId: aspect.aspectId,
      label: aspect.label,
      priority: aspect.priority,
      question: aspect.question,
      ruleId: aspect.ruleId,
    }))
    .sort((left, right) => left.priority - right.priority || left.label.localeCompare(right.label));
}

export function conceptGroundingSummariesFromPackage(
  packageData: RetrievalPackage,
): ConceptGroundingSummary[] {
  const counts = new Map<string, ConceptGroundingSummary>();
  for (const hit of packageData.hits) {
    for (const concept of conceptMatchesFromHit(hit)) {
      const key = conceptGroundingKey(concept);
      const current = counts.get(key);
      if (current) {
        current.evidenceCount += 1;
      } else {
        counts.set(key, {
          code: concept.code,
          conceptId: concept.conceptId,
          displayName: concept.displayName,
          evidenceCount: 1,
          standardSystem: concept.standardSystem,
        });
      }
    }
  }
  return [...counts.values()].sort(
    (left, right) =>
      left.standardSystem.localeCompare(right.standardSystem) ||
      left.displayName.localeCompare(right.displayName),
  );
}

export function serverSearchSignatureFromPackage(packageData: RetrievalPackage): string | null {
  return optionalStringValue(packageData.handoff_context.search_signature);
}

export function rulePackFingerprint(pack?: RuntimeRetrievalRulePack): string {
  if (!pack) return "missing";
  if (pack.content_hash) return pack.content_hash;
  if (pack.version) return pack.version;
  return `${pack.status}:${pack.rule_count}`;
}

export function conceptGroundingKey(
  concept: Pick<ConceptGroundingSummary, "code" | "conceptId" | "standardSystem">,
): string {
  return `${concept.standardSystem}:${concept.code ?? ""}:${concept.conceptId}`;
}

export function evidenceIdsFromRun(run: RetrievalSearchRun): string[] {
  return run.packageData.hits.map((hit) => hit.evidence.evidence_id);
}

export function qualitySummaryFingerprint(summary: RetrievalQualitySummary | null): string {
  if (!summary) return "none";
  return [
    summary.status,
    summary.score,
    summary.top_action,
    summary.blocker_codes.join(","),
    summary.warning_codes.join(","),
  ].join("|");
}

export function correctiveActionSummaryFromPackage(
  packageData: RetrievalPackage,
): CorrectiveActionSummary {
  const backendSummary = packageData.recommended_action_summary;
  if (backendSummary) {
    const actionTypeCounts = backendSummary.action_type_counts ?? {
      apply_filter: backendSummary.apply_filter_count,
      broaden_query: backendSummary.broaden_query_count ?? 0,
    };
    return {
      count: backendSummary.count,
      highestPriority: backendSummary.highest_priority ?? null,
      highestSeverity: backendSummary.highest_severity ?? null,
      topActionTitle: backendSummary.top_action_title ?? null,
      applyFilterCount: backendSummary.apply_filter_count,
      broadenQueryCount: backendSummary.broaden_query_count ?? actionTypeCounts.broaden_query ?? 0,
      actionTypeCounts,
    };
  }
  const actions = packageData.recommended_actions ?? [];
  const topAction = actions[0] ?? null;
  const actionTypeCounts = recommendedActionTypeCounts(actions);
  return {
    count: actions.length,
    highestPriority: topAction?.priority ?? null,
    highestSeverity: topAction?.severity ?? null,
    topActionTitle: topAction?.title ?? null,
    applyFilterCount: actionTypeCounts.apply_filter ?? 0,
    broadenQueryCount: actionTypeCounts.broaden_query ?? 0,
    actionTypeCounts,
  };
}

function coverageSummaryFromItem(
  item: RetrievalCoverage["standard_system"][number],
  group: "aspect" | "standard",
): RetrievalCoverageSummary {
  return {
    field: item.field,
    label: group === "standard" ? item.value : humanize(item.value),
    selectedCount: item.selected_count,
    status: item.status,
    suggestedFilter: stringRecordValue(item.suggested_filter),
    value: item.value,
  };
}

function coverageComparisonKey(item: RetrievalCoverageSummary): string {
  return `${item.field}:${item.value}`;
}

function rulePackStatusValue(value: unknown): RuntimeRetrievalRulePack["status"] {
  if (value === "ok" || value === "missing" || value === "error") return value;
  return "error";
}

function qualityWarningCount(signals: RetrievalQualitySignal[]): number {
  return signals.filter((signal) =>
    ["destructive", "error", "warning"].includes(signal.severity),
  ).length;
}

function conceptMatchesFromHit(hit: RetrievalHit): ConceptMatchSignal[] {
  const matches = hit.source_locator.concept_matches;
  if (!Array.isArray(matches)) return [];
  return matches
    .map((item) => recordValue(item))
    .map((item) => ({
      code: optionalStringValue(item.code),
      conceptId: stringValue(item.concept_id, ""),
      displayName: stringValue(item.display_name, "Medical concept"),
      standardSystem: stringValue(item.standard_system, "unknown"),
    }))
    .filter((item) => item.conceptId);
}

function recommendedActionTypeCounts(
  actions: RetrievalRecommendedAction[],
): Record<string, number> {
  return actions.reduce<Record<string, number>>((counts, action) => {
    counts[action.action_type] = (counts[action.action_type] ?? 0) + 1;
    return counts;
  }, {});
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

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function booleanValue(value: unknown): boolean {
  return value === true;
}

function stringRecordValue(value: unknown): Record<string, string> {
  const record = recordValue(value);
  return Object.fromEntries(
    Object.entries(record)
      .map(([key, item]) => [key.trim(), typeof item === "string" ? item.trim() : ""])
      .filter(([key, item]) => key && item),
  );
}
