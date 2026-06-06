import { humanize } from "../../../lib/utils";
import type {
  Evidence,
  RetrievalEvidenceBucket,
  RetrievalHit,
  RetrievalPackage,
  RetrievalRecommendedAction,
  RetrievalScoreComponent,
} from "../../../types";

export type EvidenceProvenanceEntry = {
  href: string | null;
  label: string;
  value: string;
};

export type EvidenceSupportStatus = "strong" | "partial" | "weak";

export type EvidenceSupportSummary = {
  aspect_count: number;
  concept_count: number;
  matched_term_count: number;
  provenance_field_count: number;
  ranking_signal_count: number;
};

export type EvidenceUseGuidance = {
  action: string;
  reasons: string[];
  status: EvidenceSupportStatus;
  title: string;
};

export type EvidenceUsabilitySummary = {
  checks: string[];
  headline: string;
  limitation: string;
  recommendation: string;
  status: EvidenceSupportStatus;
};

export type RetrievalEvidenceJudgment = {
  value: "relevant" | "partial" | "not_relevant";
};

export type EvidenceSupportMatrixRow = {
  aspectCount: number;
  bucketLabels: string[];
  conceptCount: number;
  confidenceLabel: string;
  evidenceId: string;
  judgment: RetrievalEvidenceJudgment | null;
  matchedTermCount: number;
  provenanceCount: number;
  rank: number;
  score: number;
  sourceId: string;
  sourceType: string;
  standardSystem: string | null;
  supportStatus: EvidenceSupportStatus;
};

export type EvidenceRankingBoostSignal = {
  label: string;
  reason: string;
  ruleId: string;
  weight: number | null;
};

export type EvidenceConceptMatchSignal = {
  clinicalDomain: string | null;
  code: string | null;
  conceptId: string;
  confidence: number;
  displayName: string;
  matchedAliases: string[];
  matchedFields: string[];
  matchedTerms: string[];
  reason: string;
  standardSystem: string;
};

export type EvidenceQueryAspectMatchSignal = {
  aspectId: string;
  label: string;
  matchedFilters: Record<string, string>;
  matchedTerms: string[];
  priority: number;
  reason: string;
  ruleId: string;
};

export type EvidenceHitMatchExplanation = {
  aspectIds: string[];
  aspectLabels: string[];
  bucketIds: string[];
  bucketLabels: string[];
  conceptIds: string[];
  conceptLabels: string[];
  matchedTerms: string[];
  provenanceCount: number;
  provenanceFields: string[];
  rankingSignalCount: number;
  rankingSignalRuleIds: string[];
  supportStatus: EvidenceSupportStatus;
  topScoreComponent: {
    component: string;
    label: string;
    rank: number | null;
    value: number;
  } | null;
  topScoreDriver: string | null;
};

export type EvidenceHitSignals = {
  conceptMatches: EvidenceConceptMatchSignal[];
  queryAspectMatches: EvidenceQueryAspectMatchSignal[];
  rankingBoostSignals: EvidenceRankingBoostSignal[];
  scoreComponents: RetrievalScoreComponent[];
};

export function evidenceSignalsFromHit(hit: RetrievalHit): EvidenceHitSignals {
  return {
    conceptMatches: conceptMatchesFromHit(hit),
    queryAspectMatches: queryAspectMatchesFromHit(hit),
    rankingBoostSignals: rankingBoostSignalsFromHit(hit),
    scoreComponents: scoreComponentsFromHit(hit),
  };
}

export function scoreComponentsFromHit(hit: RetrievalHit): RetrievalScoreComponent[] {
  return (hit.score_components ?? [])
    .map((component) => ({
      component: stringValue(component.component, ""),
      description: stringValue(
        component.description,
        "Score component contribution.",
      ),
      label: stringValue(component.label, humanize(component.component)),
      metadata: recordValue(component.metadata),
      rank: typeof component.rank === "number" ? component.rank : null,
      value: numberValue(component.value) ?? 0,
    }))
    .filter((component) => component.component);
}

export function hitMatchExplanation({
  buckets,
  hit,
  provenanceEntries,
  signals,
}: {
  buckets: RetrievalEvidenceBucket[];
  hit: RetrievalHit;
  provenanceEntries: EvidenceProvenanceEntry[];
  signals: EvidenceHitSignals;
}): EvidenceHitMatchExplanation {
  const evidenceId = hit.evidence.evidence_id;
  const bucketLabels = buckets
    .filter((bucket) => bucket.evidence_ids.includes(evidenceId))
    .map((bucket) => bucket.label);
  const matchedBuckets = buckets.filter((bucket) =>
    bucket.evidence_ids.includes(evidenceId),
  );
  const topComponent = [...signals.scoreComponents].sort(
    (left, right) => Math.abs(right.value) - Math.abs(left.value),
  )[0];
  const supportSummary = evidenceSupportSummary({
    hit,
    provenanceEntries,
    signals,
  });
  const backendExplanation = recordValue(hit.match_explanation);
  const backendTopComponent = recordValue(backendExplanation.top_score_component);
  return {
    aspectIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.aspect_ids).slice(0, 8),
      uniqueValues(
        signals.queryAspectMatches.map((match) => match.aspectId),
      ).slice(0, 8),
    ),
    aspectLabels: nonEmptyStringArray(
      stringArrayValue(backendExplanation.aspect_labels).slice(0, 4),
      uniqueValues(signals.queryAspectMatches.map((match) => match.label)).slice(
        0,
        4,
      ),
    ),
    bucketIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.bucket_ids).slice(0, 8),
      uniqueValues(matchedBuckets.map((bucket) => bucket.bucket_id)).slice(0, 8),
    ),
    bucketLabels: nonEmptyStringArray(
      stringArrayValue(backendExplanation.bucket_labels).slice(0, 4),
      uniqueValues(bucketLabels).slice(0, 4),
    ),
    conceptIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.concept_ids).slice(0, 8),
      uniqueValues(signals.conceptMatches.map((match) => match.conceptId)).slice(
        0,
        8,
      ),
    ),
    conceptLabels: nonEmptyStringArray(
      stringArrayValue(backendExplanation.concept_labels).slice(0, 4),
      uniqueValues(
        signals.conceptMatches.map((match) =>
          match.code ? `${match.standardSystem} ${match.code}` : match.displayName,
        ),
      ).slice(0, 4),
    ),
    matchedTerms: nonEmptyStringArray(
      stringArrayValue(backendExplanation.matched_terms).slice(0, 6),
      uniqueValues(hit.matched_terms).slice(0, 6),
    ),
    provenanceCount:
      numberValue(backendExplanation.provenance_count) ?? provenanceEntries.length,
    provenanceFields: nonEmptyStringArray(
      stringArrayValue(backendExplanation.provenance_fields).slice(0, 12),
      uniqueValues(provenanceEntries.map((entry) => entry.label)).slice(0, 12),
    ),
    rankingSignalCount:
      numberValue(backendExplanation.ranking_signal_count) ??
      signals.rankingBoostSignals.length,
    rankingSignalRuleIds: nonEmptyStringArray(
      stringArrayValue(backendExplanation.ranking_signal_rule_ids).slice(0, 12),
      uniqueValues(signals.rankingBoostSignals.map((signal) => signal.ruleId)).slice(
        0,
        12,
      ),
    ),
    supportStatus:
      hitSupportStatusValue(backendExplanation.support_status) ??
      evidenceSupportStatus(supportSummary),
    topScoreComponent: backendTopComponent.component
      ? {
          component: stringValue(backendTopComponent.component, ""),
          label: stringValue(backendTopComponent.label, "Score component"),
          rank: numberValue(backendTopComponent.rank),
          value: numberValue(backendTopComponent.value) ?? 0,
        }
      : topComponent
        ? {
            component: topComponent.component,
            label: topComponent.label,
            rank: topComponent.rank ?? null,
            value: topComponent.value,
          }
        : null,
    topScoreDriver:
      optionalStringValue(backendExplanation.top_score_driver) ??
      (topComponent
        ? `${topComponent.label} ${formatSignedDelta(topComponent.value)}`
        : null),
  };
}

export function rankingBoostSignalsFromHit(
  hit: RetrievalHit,
): EvidenceRankingBoostSignal[] {
  const detailedSignals = rankingBoostDetailsValue(hit.source_locator.ranking_boosts);
  if (detailedSignals.length) return detailedSignals;
  return stringArrayValue(hit.source_locator.ranking_boost_rules).map((ruleId) => ({
    label: formatRankingSignal(ruleId),
    reason: "Ranking boost rule applied.",
    ruleId,
    weight: null,
  }));
}

export function queryAspectMatchesFromHit(
  hit: RetrievalHit,
): EvidenceQueryAspectMatchSignal[] {
  const matches = hit.source_locator.query_aspect_matches;
  if (!Array.isArray(matches)) return [];
  return matches
    .map((item) => recordValue(item))
    .map((item) => ({
      aspectId: stringValue(item.aspect_id, ""),
      label: stringValue(item.label, "Search aspect"),
      matchedFilters: stringRecordValue(item.matched_filters),
      matchedTerms: stringArrayValue(item.matched_terms),
      priority: numberValue(item.priority) ?? 100,
      reason: stringValue(item.reason, "Evidence matched this search aspect."),
      ruleId: stringValue(item.rule_id, ""),
    }))
    .filter((item) => item.aspectId && item.ruleId);
}

export function conceptMatchesFromHit(hit: RetrievalHit): EvidenceConceptMatchSignal[] {
  const matches = hit.source_locator.concept_matches;
  if (!Array.isArray(matches)) return [];
  return matches
    .map((item) => recordValue(item))
    .map((item) => ({
      clinicalDomain: optionalStringValue(item.clinical_domain),
      code: optionalStringValue(item.code),
      conceptId: stringValue(item.concept_id, ""),
      confidence: numberValue(item.confidence) ?? 0,
      displayName: stringValue(item.display_name, "Medical concept"),
      matchedAliases: stringArrayValue(item.matched_aliases),
      matchedFields: stringArrayValue(item.matched_fields),
      matchedTerms: stringArrayValue(item.matched_terms),
      reason: stringValue(item.reason, "Evidence supports this detected concept."),
      standardSystem: stringValue(item.standard_system, "unknown"),
    }))
    .filter((item) => item.conceptId && item.standardSystem !== "unknown");
}

export function provenanceEntriesFromEvidence(
  evidence: Evidence,
): EvidenceProvenanceEntry[] {
  const locator = evidence.locator;
  const entries: EvidenceProvenanceEntry[] = [];
  const sourceVersion = optionalStringValue(evidence.source_version);
  if (sourceVersion) entries.push({ href: null, label: "Version", value: sourceVersion });
  const locatorFields: Array<[string, string]> = [
    ["Standard", "standard"],
    ["System", "standard_system"],
    ["URL", "url"],
    ["Path", "path"],
    ["API", "api"],
    ["PMID", "pmid"],
    ["DOI", "doi"],
    ["Resource", "resource"],
    ["Table", "table"],
    ["Document", "document_id"],
    ["Chunk", "chunk_id"],
  ];
  for (const [label, key] of locatorFields) {
    const value = locatorSummaryValue(locator[key]);
    if (value) {
      entries.push({ href: provenanceHrefForLocator(key, value), label, value });
    }
  }
  return uniqueProvenanceEntries(entries).slice(0, 8);
}

export function provenanceHrefForLocator(key: string, value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  if ((key === "url" || key === "api") && /^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }
  if (key === "doi") return `https://doi.org/${encodeURIComponent(trimmed)}`;
  if (key === "pmid" && /^[0-9]+$/.test(trimmed)) {
    return `https://pubmed.ncbi.nlm.nih.gov/${trimmed}/`;
  }
  return null;
}

export function evidenceSupportSummary({
  hit,
  provenanceEntries,
  signals,
}: {
  hit: RetrievalHit;
  provenanceEntries: EvidenceProvenanceEntry[];
  signals: EvidenceHitSignals;
}): EvidenceSupportSummary {
  return {
    aspect_count: signals.queryAspectMatches.length,
    concept_count: signals.conceptMatches.length,
    matched_term_count: hit.matched_terms.length,
    provenance_field_count: provenanceEntries.length,
    ranking_signal_count: signals.rankingBoostSignals.length,
  };
}

export function evidenceSupportMatrixRows({
  formatConfidence,
  packageData,
  relevanceJudgments,
  runId,
  standardSystemValue,
  summaryForHit,
}: {
  formatConfidence: (confidence: number | null | undefined) => string;
  packageData: RetrievalPackage;
  relevanceJudgments: Record<string, RetrievalEvidenceJudgment | null | undefined>;
  runId: string | null;
  standardSystemValue: (value: unknown) => string | null;
  summaryForHit: (
    hit: RetrievalHit,
    provenanceEntries: EvidenceProvenanceEntry[],
  ) => EvidenceSupportSummary;
}): EvidenceSupportMatrixRow[] {
  const bucketLabelsByEvidenceId = evidenceBucketLabelsByEvidenceId(
    packageData.evidence_buckets ?? [],
  );
  return packageData.hits.map((hit, index) => {
    const provenanceEntries = provenanceEntriesFromEvidence(hit.evidence);
    const summary = summaryForHit(hit, provenanceEntries);
    const judgment = runId
      ? relevanceJudgments[`${runId}:${hit.evidence.evidence_id}`] ?? null
      : null;
    return {
      aspectCount: summary.aspect_count,
      bucketLabels: bucketLabelsByEvidenceId.get(hit.evidence.evidence_id) ?? [],
      conceptCount: summary.concept_count,
      confidenceLabel: formatConfidence(hit.evidence.confidence),
      evidenceId: hit.evidence.evidence_id,
      judgment,
      matchedTermCount: summary.matched_term_count,
      provenanceCount: summary.provenance_field_count,
      rank: index + 1,
      score: hit.score,
      sourceId: hit.evidence.source_id,
      sourceType: String(hit.evidence.source_type),
      standardSystem: standardSystemValue(hit.evidence.locator.standard_system),
      supportStatus: evidenceSupportStatus(summary),
    };
  });
}

export function evidenceSupportStatus(
  summary: EvidenceSupportSummary,
): EvidenceSupportStatus {
  if (
    summary.matched_term_count > 0 &&
    summary.provenance_field_count > 0 &&
    (summary.concept_count > 0 || summary.aspect_count > 0)
  ) {
    return "strong";
  }
  if (summary.matched_term_count > 0 || summary.provenance_field_count > 0) {
    return "partial";
  }
  return "weak";
}

export function evidenceUseGuidance({
  explanation,
  judgment,
  judgmentLabel,
  summary,
}: {
  explanation: EvidenceHitMatchExplanation;
  judgment: RetrievalEvidenceJudgment | null;
  judgmentLabel: (value: RetrievalEvidenceJudgment["value"]) => string;
  summary: EvidenceSupportSummary;
}): EvidenceUseGuidance {
  const reasons = evidenceUseGuidanceReasons({
    explanation,
    judgment,
    judgmentLabel,
    summary,
  });
  if (explanation.supportStatus === "strong" && judgment?.value !== "not_relevant") {
    return {
      action:
        "Good candidate for evidence review. Confirm the claim and provenance before using it in a workflow explanation.",
      reasons,
      status: "strong",
      title: "Use with provenance check",
    };
  }
  if (explanation.supportStatus === "partial") {
    return {
      action:
        "Needs review before use. It has some support, but missing grounding or traceability can make the explanation weak.",
      reasons,
      status: "partial",
      title: "Review before relying on it",
    };
  }
  return {
    action:
      "Treat as weak support. Broaden or adjust the query, inspect source scope, or mark the hit not relevant if it does not answer the submitted question.",
    reasons,
    status: "weak",
    title: "Weak evidence support",
  };
}

export function evidenceUsabilitySummary({
  explanation,
  formatCount,
  judgment,
  judgmentLabel,
  summary,
}: {
  explanation: EvidenceHitMatchExplanation;
  formatCount: (count: number, singular: string) => string;
  judgment: RetrievalEvidenceJudgment | null;
  judgmentLabel: (value: RetrievalEvidenceJudgment["value"]) => string;
  summary: EvidenceSupportSummary;
}): EvidenceUsabilitySummary {
  const status = evidenceSupportStatus(summary);
  const guidance = evidenceUseGuidance({
    explanation,
    judgment,
    judgmentLabel,
    summary,
  });
  const traceability =
    summary.provenance_field_count > 0
      ? `${formatCount(summary.provenance_field_count, "provenance field")}`
      : "missing provenance";
  const grounding =
    summary.concept_count > 0 || summary.aspect_count > 0
      ? `${formatCount(
          summary.concept_count + summary.aspect_count,
          "grounding signal",
        )}`
      : "missing medical grounding";
  const judgmentLabelText = judgment
    ? `operator judged ${judgmentLabel(judgment.value)}`
    : "not operator-judged";
  const headline =
    status === "strong"
      ? "This result has enough support signals for operator evidence review."
      : status === "partial"
        ? "This result has partial support and needs review before use."
        : "This result is weak support for the submitted search.";
  const limitation =
    status === "strong"
      ? "Still verify the claim text and source locator before using it in an explanation."
      : summary.provenance_field_count === 0
        ? "Traceability is limited because no provenance field is available."
        : "Medical grounding or exact query support is incomplete.";

  return {
    checks: [
      `${formatCount(summary.matched_term_count, "matched term")}`,
      traceability,
      grounding,
      judgmentLabelText,
      explanation.bucketLabels.length
        ? "evidence bucket matched"
        : "not in evidence bucket",
    ],
    headline,
    limitation,
    recommendation: guidance.action,
    status,
  };
}

export function evidenceReportFromHit({
  formatClaim,
  hit,
  judgment,
  matchExplanation,
  provenanceEntries,
  recommendedActions = [],
  signals,
  supportSummary,
  usabilitySummary,
}: {
  formatClaim: (claim: string) => string;
  hit: RetrievalHit;
  judgment: RetrievalEvidenceJudgment | null;
  matchExplanation: EvidenceHitMatchExplanation;
  provenanceEntries: EvidenceProvenanceEntry[];
  recommendedActions?: RetrievalRecommendedAction[];
  signals: EvidenceHitSignals;
  supportSummary: EvidenceSupportSummary;
  usabilitySummary: EvidenceUsabilitySummary;
}) {
  const correctiveActions = correctiveActionReportContext(hit, recommendedActions);
  return {
    report_type: "retrieval_evidence_hit",
    version: 1,
    generated_at: new Date().toISOString(),
    evidence: {
      evidence_id: hit.evidence.evidence_id,
      source_id: hit.evidence.source_id,
      source_type: hit.evidence.source_type,
      source_version: hit.evidence.source_version ?? null,
      trust_level: hit.evidence.trust_level,
      confidence: hit.evidence.confidence ?? null,
      claim: formatClaim(hit.evidence.claim),
    },
    support_summary: supportSummary,
    usability_summary: usabilitySummary,
    match_explanation: matchExplanation,
    ranking: {
      score: hit.score,
      lexical_score: hit.lexical_score,
      vector_score: hit.vector_score,
      rerank_score: hit.rerank_score,
      matched_terms: hit.matched_terms,
      score_components: signals.scoreComponents,
      ranking_boosts: signals.rankingBoostSignals,
    },
    grounding: {
      concept_matches: signals.conceptMatches,
      query_aspect_matches: signals.queryAspectMatches,
    },
    provenance: {
      summary: provenanceEntries,
      locator: hit.evidence.locator,
      source_locator: hit.source_locator,
    },
    corrective_actions: correctiveActions,
    snippet: hit.snippet,
  };
}

function evidenceUseGuidanceReasons({
  explanation,
  judgment,
  judgmentLabel,
  summary,
}: {
  explanation: EvidenceHitMatchExplanation;
  judgment: RetrievalEvidenceJudgment | null;
  judgmentLabel: (value: RetrievalEvidenceJudgment["value"]) => string;
  summary: EvidenceSupportSummary;
}): string[] {
  const reasons: string[] = [];
  if (summary.matched_term_count > 0) reasons.push("terms matched");
  else reasons.push("no exact terms");
  if (summary.provenance_field_count > 0) reasons.push("provenance present");
  else reasons.push("missing provenance");
  if (summary.concept_count > 0) reasons.push("concept grounded");
  if (summary.aspect_count > 0) reasons.push("query aspect supported");
  if (summary.concept_count === 0 && summary.aspect_count === 0) {
    reasons.push("missing medical grounding");
  }
  if (summary.ranking_signal_count > 0) reasons.push("ranking rule support");
  if (judgment) reasons.push(`judged ${judgmentLabel(judgment.value)}`);
  else reasons.push("unjudged");
  if (explanation.bucketLabels.length) reasons.push("evidence bucket matched");
  else reasons.push("not in evidence bucket");
  return reasons.slice(0, 8);
}

function correctiveActionReportContext(
  hit: RetrievalHit,
  actions: RetrievalRecommendedAction[],
) {
  return {
    related_to_evidence: actions
      .filter((action) => action.evidence_ids.includes(hit.evidence.evidence_id))
      .slice(0, 6)
      .map(correctiveActionReportItem),
    package_top_actions: actions.slice(0, 6).map(correctiveActionReportItem),
  };
}

function correctiveActionReportItem(action: RetrievalRecommendedAction) {
  return {
    action_id: action.action_id,
    priority: action.priority,
    severity: action.severity,
    action_type: action.action_type,
    title: action.title,
    description: action.description,
    suggested_filter: action.suggested_filter,
    source_signal_codes: action.source_signal_codes,
    evidence_ids: action.evidence_ids,
    metadata: action.metadata,
  };
}

function evidenceBucketLabelsByEvidenceId(
  buckets: RetrievalEvidenceBucket[],
): Map<string, string[]> {
  const labelsByEvidenceId = new Map<string, string[]>();
  for (const bucket of buckets) {
    for (const evidenceId of bucket.evidence_ids ?? []) {
      const labels = labelsByEvidenceId.get(evidenceId) ?? [];
      labels.push(bucket.label);
      labelsByEvidenceId.set(evidenceId, labels);
    }
  }
  return labelsByEvidenceId;
}

function locatorSummaryValue(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) return value.trim();
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  if (Array.isArray(value)) {
    const items = value
      .map(locatorSummaryValue)
      .filter((item): item is string => Boolean(item));
    return items.length ? items.slice(0, 3).join(", ") : null;
  }
  return null;
}

function uniqueProvenanceEntries(
  entries: EvidenceProvenanceEntry[],
): EvidenceProvenanceEntry[] {
  const seen = new Set<string>();
  return entries.filter((entry) => {
    const key = `${entry.label}:${entry.value}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function hitSupportStatusValue(value: unknown): EvidenceSupportStatus | null {
  return value === "strong" || value === "partial" || value === "weak"
    ? value
    : null;
}

function nonEmptyStringArray(values: string[], fallback: string[]): string[] {
  return values.length ? values : fallback;
}

function rankingBoostDetailsValue(value: unknown): EvidenceRankingBoostSignal[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      label: stringValue(item.label, "Ranking boost"),
      reason: stringValue(item.reason, "Ranking boost rule applied."),
      ruleId: stringValue(item.rule_id, ""),
      weight: numberValue(item.weight),
    }))
    .filter((item) => item.ruleId);
}

function formatRankingSignal(ruleId: string): string {
  return humanize(ruleId.replace(/^boost_/, ""));
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function numberValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (item): item is string => typeof item === "string" && item.trim().length > 0,
  );
}

function stringRecordValue(value: unknown): Record<string, string> {
  const source = recordValue(value);
  return Object.fromEntries(
    Object.entries(source)
      .filter((entry): entry is [string, string] => typeof entry[1] === "string")
      .filter(([, item]) => item.trim().length > 0),
  );
}

function uniqueValues(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort();
}

function formatSignedDelta(delta: number): string {
  return delta > 0 ? `+${delta}` : String(delta);
}
