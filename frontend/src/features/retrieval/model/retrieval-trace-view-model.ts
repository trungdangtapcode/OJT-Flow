import { humanize } from "../../../lib/utils";
import type { RetrievalPackage } from "../../../types";
import type { QueryAnalysisBlockView } from "../components/query-analysis-block-types";
import type { RetrievalTracePanelView } from "../components/retrieval-trace-panel-types";
import {
  queryAspectFilterEntries,
  queryProfileFilterEntries,
} from "./retrieval-filter-model";
import { formatShortSignature } from "./retrieval-format";
import {
  queryAnalysisFromPackage,
  queryVariantsFromTrace,
  type QueryAnalysisStack,
} from "./retrieval-query-analysis";
import {
  diversityFromPackage,
  formatDiversityTrace,
  formatEmbeddingStack,
  formatFrameworkStack,
  formatQualityPolicyTrace,
  formatRerankerStack,
  qualityPolicyFromPackage,
  rankingStackFromPackage,
} from "./retrieval-runtime-stack";
import { serverSearchSignatureFromPackage } from "./retrieval-run-summary";

export function retrievalTracePanelView(
  packageData: RetrievalPackage | undefined,
): RetrievalTracePanelView | null {
  if (!packageData) return null;
  const trace = packageData.trace;
  const stack = rankingStackFromPackage(packageData);
  const diversity = diversityFromPackage(packageData);
  const qualityPolicy = qualityPolicyFromPackage(packageData);
  const queryAnalysis = queryAnalysisFromPackage(packageData);
  const searchSignature = serverSearchSignatureFromPackage(packageData);
  return {
    coverage: packageData.coverage,
    facts: [
      { label: "Strategy", value: trace.strategy },
      { label: "Candidates", value: String(trace.candidates_seen) },
      { label: "Framework", value: formatFrameworkStack(stack) },
      { label: "Embedding", value: formatEmbeddingStack(stack) },
      { label: "Reranker", value: formatRerankerStack(stack) },
      { label: "Diversity", value: formatDiversityTrace(diversity) },
      { label: "Quality policy", value: formatQualityPolicyTrace(qualityPolicy) },
      {
        label: "Search signature",
        value: searchSignature ? formatShortSignature(searchSignature) : "unknown",
      },
    ],
    filtersApplied: trace.filters_applied,
    qualitySignals: packageData.quality_signals ?? [],
    queryAnalysis: queryAnalysisBlockView(queryAnalysis, trace.filters_applied),
    queryVariants: queryVariantsFromTrace(trace),
    recommendedActions: packageData.recommended_actions ?? [],
    safetyFlags: trace.safety_flags.map(humanize),
    warnings: trace.warnings,
  };
}

function queryAnalysisBlockView(
  analysis: QueryAnalysisStack | null,
  appliedFilters: Record<string, unknown>,
): QueryAnalysisBlockView | null {
  if (!analysis) return null;
  return {
    ...analysis,
    queryAspects: analysis.queryAspects.map((aspect) => ({
      ...aspect,
      filterEntries: queryAspectFilterEntries(aspect, appliedFilters),
    })),
    queryProfileFilterEntries: analysis.queryProfile
      ? queryProfileFilterEntries(analysis.queryProfile, appliedFilters)
      : [],
    queryProfileRouteHelpText:
      "The backend route chosen for this query, such as broad, structured, or safety-sensitive search. Use this to confirm the search behavior matches the question.",
  };
}
