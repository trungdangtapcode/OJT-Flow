import type { RetrievalPackage, RetrievalSearchPayload } from "../../../types";
import { activeFiltersFromPayload } from "./retrieval-cockpit-filter-signals";

export type RetrievalCockpitQueryHealthSignals = {
  candidateCount: number;
  exactSource: string;
  fields: string[];
  filterCount: number;
  hasClinicalContext: boolean;
  hitCount: number;
  queryTerms: string[];
  qualityStatus: string | null;
  topK: number;
  warningCount: number;
};

export function queryHealthSignalsFromPackage(
  payload: RetrievalSearchPayload | null,
  packageData: RetrievalPackage,
): RetrievalCockpitQueryHealthSignals {
  const fields = payload?.fields ?? [];
  return {
    candidateCount: packageData.trace.candidates_seen,
    exactSource: payload?.filters?.source_id ?? "",
    fields,
    filterCount: payload ? activeFiltersFromPayload(payload).length : 0,
    hasClinicalContext: Boolean(
      payload?.schema_id ||
        payload?.detected_format ||
        payload?.resource_type ||
        payload?.clinical_domain ||
        payload?.standard_system ||
        fields.length,
    ),
    hitCount: packageData.hits.length,
    queryTerms: payload?.query.trim().split(/\s+/).filter(Boolean) ?? [],
    qualityStatus: packageData.quality_summary?.status ?? null,
    topK: payload?.top_k ?? packageData.hits.length,
    warningCount:
      packageData.trace.warnings.length +
      packageData.trace.safety_flags.length +
      (packageData.quality_signals ?? []).filter((signal) => signal.severity !== "info")
        .length,
  };
}
