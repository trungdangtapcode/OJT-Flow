import type {
  RetrievalPackage,
  RetrievalQueryVariant,
} from "../../../types";
import type { QueryAnalysisStack } from "./retrieval-query-analysis-types";
import {
  recordValue,
  stringValue,
} from "./retrieval-query-analysis-coercion";

export function queryVariantsFromTrace(
  trace: RetrievalPackage["trace"],
): RetrievalQueryVariant[] {
  const detailedVariants = queryVariantDetailsValue(trace.query_variant_details);
  if (detailedVariants.length) return detailedVariants;
  return trace.query_variants.map((variant) => ({
    metadata: {},
    reason: "Legacy query variant from retrieval trace.",
    source: "legacy_trace",
    variant,
  }));
}

export function queryVariantsFromAnalysis(
  analysis: QueryAnalysisStack,
): RetrievalQueryVariant[] {
  const variants = analysis.queryVariants;
  if (variants.length) return variants;
  return analysis.queryVariantTexts.map((variant) => ({
    metadata: {},
    reason: "Query variant from retrieval plan analysis.",
    source: "query_analysis",
    variant,
  }));
}

export function queryVariantDetailsValue(value: unknown): RetrievalQueryVariant[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      metadata: recordValue(item.metadata),
      reason: stringValue(item.reason, "Query variant used for retrieval."),
      source: stringValue(item.source, "unknown"),
      variant: stringValue(item.variant, ""),
    }))
    .filter((item) => item.variant);
}
