import { humanize } from "../../../lib/utils";
import type { RetrievalPackage } from "../../../types";
import type { RetrievalCockpitRankingStack } from "./retrieval-cockpit-runtime-types";
import {
  booleanValue,
  numberValue,
  optionalBooleanValue,
  recordValue,
  stringValue,
} from "./retrieval-runtime-values";

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

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDecimal(value: number): string {
  return value.toLocaleString(undefined, {
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  });
}
