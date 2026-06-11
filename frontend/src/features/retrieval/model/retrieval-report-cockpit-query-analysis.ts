import type {
  RetrievalPackage,
  RetrievalSearchPayload,
} from "../../../types";
import { queryHealthItems } from "./retrieval-cockpit-signals";
import { queryAnalysisFromPackage } from "./retrieval-query-analysis";
import { medicalSearchHintReport } from "./retrieval-report-medical-hints";
import {
  queryAspectSummariesFromPackage,
  queryProfileSummaryFromPackage,
} from "./retrieval-run-summary";

export function retrievalCockpitQueryAnalysisReport(
  packageData: RetrievalPackage,
  submittedSearchPayload: RetrievalSearchPayload | null,
) {
  const analysis = queryAnalysisFromPackage(packageData);

  return {
    query_health: queryHealthItems(submittedSearchPayload, packageData),
    strategy: analysis.strategy,
    query_profile: queryProfileSummaryFromPackage(packageData),
    variant_count: analysis.variantCount,
    standards: analysis.standards,
    detected_concepts: analysis.detectedConcepts,
    expanded_terms: analysis.expandedTerms,
    query_aspects: queryAspectSummariesFromPackage(packageData),
    diagnostics: analysis.diagnostics.map((diagnostic) => ({
      code: diagnostic.code,
      severity: diagnostic.severity,
      message: diagnostic.message,
      suggested_action: diagnostic.suggestedAction,
      metadata: diagnostic.metadata,
    })),
    rule_ids: analysis.ruleIds,
    medical_search_hints: medicalSearchHintReport(packageData),
  };
}
