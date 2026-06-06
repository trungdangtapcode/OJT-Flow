import { humanize } from "../../../lib/utils";
import type { RetrievalPackage } from "../../../types";
import type {
  DiversitySelectionStack,
  DiversityStack,
} from "../components/source-diversity-panel";

export type RetrievalRankingStack = {
  embedding: {
    dimensions: number | null;
    model: string;
    provider: string;
  };
  framework: {
    bm25Enabled: boolean | null;
    bm25Weight: number | null;
    candidateTopK: number | null;
    filteredNodeCount: number | null;
    metadataFilterCount: number | null;
    name: string;
    nodeCount: number | null;
    vectorWeight: number | null;
  };
  reranker: {
    device: string | null;
    enabled: boolean;
    model: string;
    provider: string;
  };
};

export type RetrievalQualityPolicyStack = {
  blockingSeverities: string[];
  conceptGroundingRequirements: {
    minConfidence: number | null;
    requireDetectedConcepts: boolean | null;
  };
  provenanceRequirements: {
    locatorAnyKeys: string[];
    requireSourceVersion: boolean | null;
    sourceTypes: string[];
  };
  rankingThresholds: Record<string, number>;
  reviewScoreBelow: number | null;
  reviewSeverities: string[];
  severityPenalties: Record<string, number>;
  version: string;
};

export type RetrievalFusionDiagnosticsView = {
  interpretation: string;
  label: string;
  tone: "success" | "warning" | "info";
};

export function rankingStackFromPackage(
  packageData: RetrievalPackage,
): RetrievalRankingStack {
  const embedding = recordValue(packageData.handoff_context.embedding);
  const frameworkComponents = recordValue(packageData.handoff_context.framework_components);
  const reranker = recordValue(packageData.handoff_context.reranker);
  const rerankerProvider = stringValue(reranker.provider, "none");
  return {
    embedding: {
      dimensions: numberValue(embedding.dimensions),
      model: stringValue(embedding.model, "unknown"),
      provider: stringValue(embedding.provider, "unknown"),
    },
    framework: {
      bm25Enabled: optionalBooleanValue(frameworkComponents.bm25_enabled),
      bm25Weight: numberValue(frameworkComponents.bm25_weight),
      candidateTopK: numberValue(frameworkComponents.candidate_top_k),
      filteredNodeCount: numberValue(frameworkComponents.filtered_node_count),
      metadataFilterCount: numberValue(frameworkComponents.metadata_filter_count),
      name: stringValue(packageData.handoff_context.framework, "custom"),
      nodeCount: numberValue(frameworkComponents.node_count),
      vectorWeight: numberValue(frameworkComponents.vector_weight),
    },
    reranker: {
      device: optionalStringValue(reranker.device),
      enabled: booleanValue(reranker.enabled) && rerankerProvider !== "none",
      model: stringValue(reranker.model, "none"),
      provider: rerankerProvider,
    },
  };
}

export function diversityFromPackage(packageData: RetrievalPackage): DiversityStack {
  const diversity = recordValue(packageData.diversity ?? packageData.handoff_context.diversity);
  return {
    candidateSourceCount: numberValue(diversity.candidate_source_count) ?? 0,
    duplicateSelectedSourceCount:
      numberValue(diversity.duplicate_selected_source_count) ?? 0,
    enabled: booleanValue(diversity.enabled),
    lambda: numberValue(diversity.lambda_value) ?? numberValue(diversity.lambda),
    selectedHits: diversitySelectionDetailsValue(diversity.selected_hits),
    selectedSourceCount: numberValue(diversity.selected_source_count) ?? 0,
    selectionMode: stringValue(diversity.selection_mode, "unknown"),
  };
}

export function qualityPolicyFromPackage(
  packageData: RetrievalPackage,
): RetrievalQualityPolicyStack {
  const policy = recordValue(packageData.handoff_context.quality_policy);
  const conceptGroundingRequirements = recordValue(
    policy.concept_grounding_requirements,
  );
  const provenanceRequirements = recordValue(policy.provenance_requirements);
  return {
    blockingSeverities: stringArrayValue(policy.blocking_severities),
    conceptGroundingRequirements: {
      minConfidence: numberValue(conceptGroundingRequirements.min_confidence),
      requireDetectedConcepts: optionalBooleanValue(
        conceptGroundingRequirements.require_detected_concepts,
      ),
    },
    provenanceRequirements: {
      locatorAnyKeys: stringArrayValue(provenanceRequirements.locator_any_keys),
      requireSourceVersion: optionalBooleanValue(
        provenanceRequirements.require_source_version,
      ),
      sourceTypes: stringArrayValue(provenanceRequirements.source_types),
    },
    rankingThresholds: numericRecordValue(policy.ranking_thresholds),
    reviewScoreBelow: numberValue(policy.review_score_below),
    reviewSeverities: stringArrayValue(policy.review_severities),
    severityPenalties: numericRecordValue(policy.severity_penalties),
    version: stringValue(policy.version, "unknown"),
  };
}

export function hybridStackValue(ranking: RetrievalRankingStack): string {
  const lexical = ranking.framework.bm25Enabled ? "BM25" : "FTS";
  const vector = ranking.embedding.provider === "deterministic" ? "hash" : "vector";
  const rerank = ranking.reranker.enabled ? "+ rerank" : "";
  return `${lexical} + ${vector} ${rerank}`.trim();
}

export function fusionDiagnosticsFromPackage(
  packageData: RetrievalPackage,
): RetrievalFusionDiagnosticsView {
  const diagnostics = recordValue(packageData.trace.fusion_diagnostics);
  const overlapRatio = numberValue(diagnostics.top_overlap_ratio);
  const rankDelta = numberValue(diagnostics.mean_selected_rank_delta);
  const interpretation = stringValue(diagnostics.interpretation, "fusion diagnostics unavailable");
  if (overlapRatio === null) {
    return {
      interpretation,
      label: "unreported",
      tone: "info",
    };
  }
  const rankDeltaText = rankDelta === null ? "rank delta unknown" : `delta ${formatDecimal(rankDelta)}`;
  return {
    interpretation: `${humanize(interpretation)} / ${rankDeltaText}`,
    label: formatPercent(overlapRatio),
    tone: overlapRatio >= 0.75 ? "success" : overlapRatio <= 0.25 ? "warning" : "info",
  };
}

export function formatEmbeddingStack(stack: RetrievalRankingStack): string {
  const dimensions = stack.embedding.dimensions ? ` / ${stack.embedding.dimensions}d` : "";
  return `${stack.embedding.provider} / ${stack.embedding.model}${dimensions}`;
}

export function formatFrameworkStack(stack: RetrievalRankingStack): string {
  if (stack.framework.name !== "llamaindex") {
    return stack.framework.name;
  }
  const nodeText = stack.framework.nodeCount === null ? "unknown nodes" : `${stack.framework.nodeCount} nodes`;
  const filterText =
    stack.framework.filteredNodeCount === null
      ? "filtered scope unknown"
      : `${stack.framework.filteredNodeCount} filtered`;
  const metadataFilterText =
    stack.framework.metadataFilterCount === null
      ? "filters unknown"
      : `${stack.framework.metadataFilterCount} metadata filters`;
  const candidateText =
    stack.framework.candidateTopK === null ? "candidate pool unknown" : `top ${stack.framework.candidateTopK}`;
  const bm25Text =
    stack.framework.bm25Enabled === null
      ? "BM25 unknown"
      : stack.framework.bm25Enabled
        ? "BM25 on"
        : "BM25 off";
  const weights =
    stack.framework.vectorWeight === null || stack.framework.bm25Weight === null
      ? "weights unknown"
      : `weights ${stack.framework.vectorWeight.toFixed(2)}:${stack.framework.bm25Weight.toFixed(2)}`;
  return `${stack.framework.name} / ${nodeText} / ${filterText} / ${metadataFilterText} / ${candidateText} / ${bm25Text} / ${weights}`;
}

export function formatRerankerStack(stack: RetrievalRankingStack): string {
  if (!stack.reranker.enabled) {
    return `${stack.reranker.provider} disabled`;
  }
  const device = stack.reranker.device ? ` / ${stack.reranker.device}` : "";
  return `${stack.reranker.provider} / ${stack.reranker.model}${device}`;
}

export function formatDiversityTrace(diversity: DiversityStack): string {
  const lambda = diversity.lambda === null ? "n/a" : diversity.lambda.toFixed(2);
  const duplicateText = `${diversity.duplicateSelectedSourceCount} duplicate selected`;
  return `${diversity.selectionMode} / lambda ${lambda} / ${formatSourceCoverage(diversity)} sources / ${duplicateText}`;
}

export function formatQualityPolicyTrace(policy: RetrievalQualityPolicyStack): string {
  const warningPenalty = policy.severityPenalties.warning;
  const destructivePenalty = policy.severityPenalties.destructive;
  const minTopMatchedTerms = policy.rankingThresholds.min_top_matched_terms;
  const thresholdText =
    policy.reviewScoreBelow === null ? "review threshold unknown" : `review < ${policy.reviewScoreBelow}`;
  const matchText =
    minTopMatchedTerms === undefined
      ? null
      : `top match >= ${minTopMatchedTerms}`;
  const conceptText =
    policy.conceptGroundingRequirements.requireDetectedConcepts === true
      ? `concepts >= ${(policy.conceptGroundingRequirements.minConfidence ?? 0).toFixed(2)}`
      : null;
  const provenanceText = policy.provenanceRequirements.sourceTypes.length
    ? `provenance ${policy.provenanceRequirements.sourceTypes.length} source types`
    : null;
  const penaltyText = [
    warningPenalty === undefined ? null : `warning -${warningPenalty}`,
    destructivePenalty === undefined ? null : `blocker -${destructivePenalty}`,
  ].filter(Boolean);
  return [policy.version, thresholdText, matchText, conceptText, provenanceText, ...penaltyText]
    .filter(Boolean)
    .join(" / ");
}

function diversitySelectionDetailsValue(value: unknown): DiversitySelectionStack[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      evidenceId: stringValue(item.evidence_id, ""),
      originalRank: numberValue(item.original_rank) ?? 0,
      reason: stringValue(item.reason, "Selected retrieval evidence."),
      redundancyScore: numberValue(item.redundancy_score) ?? 0,
      relevanceScore: numberValue(item.relevance_score) ?? 0,
      selectedRank: numberValue(item.selected_rank) ?? 0,
      selectionScore: numberValue(item.selection_score) ?? 0,
      sourceId: stringValue(item.source_id, ""),
    }))
    .filter((item) => item.evidenceId && item.selectedRank > 0);
}

export function formatSourceCoverage(diversity: DiversityStack): string {
  return `${diversity.selectedSourceCount}/${diversity.candidateSourceCount}`;
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDecimal(value: number): string {
  return Number.isFinite(value) ? value.toFixed(3) : "n/a";
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

function optionalBooleanValue(value: unknown): boolean | null {
  if (value === true) return true;
  if (value === false) return false;
  return null;
}

function stringArrayValue(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function numericRecordValue(value: unknown): Record<string, number> {
  const record = recordValue(value);
  return Object.fromEntries(
    Object.entries(record)
      .map(([key, item]) => [key, numberValue(item)] as const)
      .filter((entry): entry is readonly [string, number] => entry[1] !== null),
  );
}
