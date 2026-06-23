import type { RetrievalRankingStack } from "./retrieval-runtime-ranking-types";

export function hybridStackValue(ranking: RetrievalRankingStack): string {
  const lexical = ranking.framework.bm25Enabled ? "BM25" : "FTS";
  const vector = "vector";
  const rerank = ranking.reranker.enabled ? "+ rerank" : "";
  return `${lexical} + ${vector} ${rerank}`.trim();
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
