import type { RetrievalSummaryStripViewModel } from "../components/retrieval-summary-strip";
import type {
  RetrievalPackage,
  RetrievalSource,
  RuntimeConfig,
} from "../../../types";
import { humanize } from "../../../lib/utils";
import { formatSourceCoverage, rankingStackFromPackage } from "./retrieval-runtime-stack";
import { diversityFromPackage } from "./retrieval-runtime-stack";
import type { RetrievalRuntimeStatusView } from "./retrieval-runtime-status-model";
import { qualitySummaryTone } from "./search-run-presentation";

export function retrievalSummaryStripView({
  packageData,
  runtime,
  sources,
  sourcesLoading,
}: {
  packageData: RetrievalPackage | undefined;
  runtime: RuntimeConfig | undefined;
  sources: RetrievalSource[];
  sourcesLoading: boolean;
}): RetrievalSummaryStripViewModel {
  const graph = packageData?.handoff_context.graph_context;
  const packageRuntime = packageData ? rankingStackFromPackage(packageData) : null;
  const diversity = packageData ? diversityFromPackage(packageData) : null;
  const qualitySummary = packageData?.quality_summary ?? null;
  const rerankerEnabled = Boolean(
    packageRuntime?.reranker.enabled ?? runtime?.rerank?.enabled,
  );
  const embeddingProvider = packageRuntime?.embedding.provider ?? runtime?.embedding.provider;
  const rerankerProvider = packageRuntime?.reranker.provider ?? runtime?.rerank?.provider;

  return {
    coverageSupporting: diversity
      ? `${diversity.selectedSourceCount} selected unique sources`
      : embeddingProvider
        ? `${embeddingProvider} embeddings`
        : "Runtime loading",
    coverageValue: diversity ? formatSourceCoverage(diversity) : graph?.nodes.length ?? 0,
    hitSupporting: packageData ? packageData.trace.strategy : "No search yet",
    hitValue: packageData?.hits.length ?? 0,
    readinessSupporting: qualitySummary?.top_action ?? "Run search to assess package quality",
    readinessTone: qualitySummaryTone(qualitySummary),
    readinessValue: qualitySummary ? `${qualitySummary.score}/100` : "n/a",
    rerankerEnabled,
    rerankerSupporting: rerankerProvider
      ? rerankerEnabled
        ? `${rerankerProvider} second stage`
        : `${rerankerProvider} disabled`
      : "Runtime loading",
    sourceCount: sources.length,
    sourcesLoading,
  };
}

export function retrievalRuntimeStatusStripView({
  integrityStatus,
  packageData,
}: {
  integrityStatus: string;
  packageData: RetrievalPackage | undefined;
}): RetrievalRuntimeStatusView | null {
  if (!packageData) return null;
  const graphContext = packageData.handoff_context.graph_context;
  const ranking = rankingStackFromPackage(packageData);
  const diversity = diversityFromPackage(packageData);
  return {
    graphEdgeCount: graphContext?.edges.length ?? null,
    graphNodeCount: graphContext?.nodes.length ?? null,
    graphTripleCount: graphContext?.triples.length ?? null,
    integrityStatus,
    rerankerEnabled: ranking.reranker.enabled,
    retrievalMode: humanize(ranking.framework.name || packageData.trace.strategy),
    sourceCoverageLabel: formatSourceCoverage(diversity),
    sourceDiversityEnabled: diversity.enabled,
  };
}
