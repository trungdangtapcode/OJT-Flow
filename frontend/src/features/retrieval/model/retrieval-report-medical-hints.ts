import type { RetrievalPackage } from "../../../types";
import { queryAnalysisFromPackage } from "./retrieval-query-analysis";
import {
  optionalStringValue,
  searchHintLineageFollowup,
  searchHintParameterExamples,
  stringArrayValue,
} from "./retrieval-report-values";

export function medicalSearchHintReport(packageData: RetrievalPackage) {
  const analysis = queryAnalysisFromPackage(packageData);
  if (!analysis.searchHints.length) {
    return [];
  }
  return analysis.searchHints.slice(0, 8).map((hint) => {
    const metadata = hint.metadata;
    return {
      target: hint.target,
      query: hint.query,
      url: hint.url,
      rationale: hint.rationale,
      warnings: hint.warnings,
      route_details: {
        endpoint_scope: stringArrayValue(metadata.scope_endpoints).slice(0, 8),
        selected_terms: stringArrayValue(metadata.selected_terms).slice(0, 8),
        selected_unit_candidates: stringArrayValue(
          metadata.selected_unit_candidates,
        ).slice(0, 8),
        parameter_examples: searchHintParameterExamples(
          metadata.parameter_examples,
        ).slice(0, 8),
        lineage_followup: searchHintLineageFollowup(
          metadata.lineage_followup,
        ).slice(0, 4),
        launchable:
          metadata.launchable === undefined ? Boolean(hint.url) : Boolean(metadata.launchable),
        capability_warning: optionalStringValue(metadata.capability_warning),
      },
    };
  });
}
