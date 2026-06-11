import type { RetrievalPackage } from "../../../types";
import {
  hybridStackValue,
  rankingStackFromPackage,
} from "./retrieval-runtime-stack";

export function retrievalCockpitRankingStackReport(packageData: RetrievalPackage) {
  const ranking = rankingStackFromPackage(packageData);

  return {
    embedding: ranking.embedding,
    framework: ranking.framework,
    reranker: ranking.reranker,
    hybrid_label: hybridStackValue(ranking),
    fusion_diagnostics: packageData.trace.fusion_diagnostics ?? {},
  };
}
