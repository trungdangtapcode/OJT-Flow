import type { RetrievalFacets } from "../../../types";
import type { RetrievalSearchRun } from "./retrieval-run-summary";
import type {
  RetrievalFacetComparison,
  RetrievalFacetConfig,
  RetrievalFacetField,
} from "./retrieval-run-comparison-types";

export function facetComparisonsBetweenRuns(
  activeRun: RetrievalSearchRun,
  baselineRun: RetrievalSearchRun,
  facetConfigs: RetrievalFacetConfig[],
): RetrievalFacetComparison[] {
  return facetConfigs.map((config) => {
    const activeValues = facetValuesFromRun(activeRun, config.field);
    const baselineValues = facetValuesFromRun(baselineRun, config.field);
    const activeSet = new Set(activeValues);
    const baselineSet = new Set(baselineValues);
    return {
      activeCount: activeValues.length,
      addedValues: activeValues.filter((value) => !baselineSet.has(value)),
      baselineCount: baselineValues.length,
      field: config.field,
      label: config.label,
      removedValues: baselineValues.filter((value) => !activeSet.has(value)),
      retainedValues: activeValues.filter((value) => baselineSet.has(value)),
    };
  });
}

export function facetValuesFromRun(
  run: RetrievalSearchRun,
  field: RetrievalFacetField,
): string[] {
  const facets = run.packageData.facets;
  if (!facets) return [];
  const buckets = facetBuckets(facets, field);
  return buckets
    .map((bucket) => bucket.value)
    .filter(Boolean)
    .sort((left, right) => left.localeCompare(right));
}

function facetBuckets(facets: RetrievalFacets, field: RetrievalFacetField) {
  if (field === "clinical_domain") return facets.clinical_domain;
  if (field === "standard_system") return facets.standard_system;
  if (field === "source_type") return facets.source_type;
  if (field === "trust_level") return facets.trust_level;
  return [];
}
