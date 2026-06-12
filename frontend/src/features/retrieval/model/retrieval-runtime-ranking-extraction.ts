import type { RetrievalPackage } from "../../../types";
import {
  booleanValue,
  numberValue,
  optionalBooleanValue,
  optionalStringValue,
  recordValue,
  stringValue,
} from "./retrieval-runtime-values";
import type { RetrievalRankingStack } from "./retrieval-runtime-ranking-types";

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
