import { humanize } from "../../../lib/utils";
import type { RetrievalPackage } from "../../../types";

export type RetrievalCockpitDiversitySelection = {
  evidenceId: string;
  originalRank: number;
  reason: string;
  redundancyScore: number;
  relevanceScore: number;
  selectedRank: number;
  selectionScore: number;
  sourceId: string;
};

export type RetrievalCockpitDiversityStack = {
  candidateSourceCount: number;
  duplicateSelectedSourceCount: number;
  enabled: boolean;
  lambda: number | null;
  selectedHits: RetrievalCockpitDiversitySelection[];
  selectedSourceCount: number;
  selectionMode: string;
};

export type RetrievalCockpitRankingStack = {
  embedding: {
    model: string;
    provider: string;
  };
  framework: {
    bm25Enabled: boolean | null;
  };
  reranker: {
    enabled: boolean;
  };
};

export type RetrievalCockpitQueryAnalysisStack = {
  detectedConcepts: string[];
  diagnostics: RetrievalCockpitQueryDiagnostic[];
  expandedTerms: string[];
  queryAspects: {
    aspectId: string;
    label: string;
    priority: number;
    question: string;
  }[];
  queryProfile: {
    complexity: string;
    label: string;
    retrievalMode: string;
    route: string;
  } | null;
  standards: string[];
  strategy: string;
  variantCount: number;
};

export type RetrievalCockpitQueryDiagnostic = {
  code: string;
  message: string;
  severity: string;
  suggestedAction: string;
};

export function rankingStackFromPackage(
  packageData: RetrievalPackage,
): RetrievalCockpitRankingStack {
  const embedding = recordValue(packageData.handoff_context.embedding);
  const frameworkComponents = recordValue(packageData.handoff_context.framework_components);
  const reranker = recordValue(packageData.handoff_context.reranker);
  const rerankerProvider = stringValue(reranker.provider, "none");
  return {
    embedding: {
      model: stringValue(embedding.model, "unknown"),
      provider: stringValue(embedding.provider, "unknown"),
    },
    framework: {
      bm25Enabled: optionalBooleanValue(frameworkComponents.bm25_enabled),
    },
    reranker: {
      enabled: booleanValue(reranker.enabled) && rerankerProvider !== "none",
    },
  };
}

export function queryAnalysisFromPackage(
  packageData: RetrievalPackage,
): RetrievalCockpitQueryAnalysisStack {
  const queryAnalysis = recordValue(packageData.handoff_context.query_analysis);
  return {
    detectedConcepts: stringArrayValue(queryAnalysis.detected_concepts),
    diagnostics: queryDiagnosticsValue(queryAnalysis.diagnostics),
    expandedTerms: stringArrayValue(queryAnalysis.expanded_terms),
    queryAspects: queryAspectsValue(queryAnalysis.query_aspects),
    queryProfile: queryProfileValue(queryAnalysis.query_profile),
    standards: stringArrayValue(queryAnalysis.standards),
    strategy: stringValue(queryAnalysis.strategy, "unknown"),
    variantCount: stringArrayValue(queryAnalysis.query_variants).length,
  };
}

export function diversityFromPackage(
  packageData: RetrievalPackage,
): RetrievalCockpitDiversityStack {
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

export function coverageGapCountFromPackage(packageData: RetrievalPackage): number {
  const coverage = packageData.coverage;
  return [...(coverage?.standard_system ?? []), ...(coverage?.query_aspects ?? [])]
    .filter((item) => item.selected_count === 0)
    .length;
}

export function conceptGroundingCountFromPackage(packageData: RetrievalPackage): number {
  const conceptKeys = new Set<string>();
  for (const hit of packageData.hits) {
    const explanation = recordValue(hit.match_explanation);
    for (const conceptId of stringArrayValue(explanation.concept_ids)) {
      conceptKeys.add(conceptId);
    }
  }
  return conceptKeys.size;
}

export function fusionDiagnosticsFromPackage(packageData: RetrievalPackage): {
  interpretation: string;
  label: string;
  tone: "success" | "warning" | "info";
} {
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

export function hybridStackValue(ranking: RetrievalCockpitRankingStack): string {
  const lexical = ranking.framework.bm25Enabled ? "BM25" : "FTS";
  const vector = ranking.embedding.provider === "deterministic" ? "hash" : "vector";
  const rerank = ranking.reranker.enabled ? "+ rerank" : "";
  return `${lexical} + ${vector} ${rerank}`.trim();
}

function queryAspectsValue(
  value: unknown,
): RetrievalCockpitQueryAnalysisStack["queryAspects"] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      aspectId: stringValue(item.aspect_id, "aspect"),
      label: stringValue(item.label, "Query aspect"),
      priority: numberValue(item.priority) ?? 100,
      question: stringValue(item.question, "Review this retrieval aspect."),
    }))
    .filter((item) => item.aspectId !== "aspect");
}

function queryProfileValue(
  value: unknown,
): RetrievalCockpitQueryAnalysisStack["queryProfile"] {
  const profile = recordValue(value);
  const profileId = optionalStringValue(profile.profile_id);
  if (!profileId) return null;
  return {
    complexity: stringValue(profile.complexity, "standard"),
    label: stringValue(profile.label, humanize(profileId)),
    retrievalMode: stringValue(profile.retrieval_mode, "hybrid"),
    route: stringValue(profile.route, profileId),
  };
}

function queryDiagnosticsValue(value: unknown): RetrievalCockpitQueryDiagnostic[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      code: stringValue(item.code, "query_diagnostic"),
      message: stringValue(item.message, "Query diagnostic unavailable."),
      severity: stringValue(item.severity, "info"),
      suggestedAction: stringValue(item.suggested_action, "Review the retrieval query."),
    }))
    .filter((item) => item.code !== "query_diagnostic");
}

function diversitySelectionDetailsValue(
  value: unknown,
): RetrievalCockpitDiversitySelection[] {
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

function optionalBooleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDecimal(value: number): string {
  return value.toLocaleString(undefined, {
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  });
}
