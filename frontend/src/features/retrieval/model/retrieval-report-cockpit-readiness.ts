import type {
  RetrievalPackage,
  RetrievalSearchPayload,
} from "../../../types";
import {
  queryHealthItems,
  searchReadinessChecklist,
} from "./retrieval-cockpit-signals";
import { retrievalDiversityReport } from "./retrieval-report-diversity";
import {
  conceptGroundingSummariesFromPackage,
  coverageSummariesFromPackage,
} from "./retrieval-run-summary";
import { diversityFromPackage } from "./retrieval-runtime-stack";

export function retrievalCockpitReadinessReport(
  packageData: RetrievalPackage,
  submittedSearchPayload: RetrievalSearchPayload | null,
) {
  const requiredBuckets =
    packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];

  return {
    readiness_checklist: searchReadinessChecklist({
      diversity: diversityFromPackage(packageData),
      packageData,
      queryHealth: queryHealthItems(submittedSearchPayload, packageData),
      requiredBuckets,
      topAction: (packageData.recommended_actions ?? [])[0] ?? null,
    }),
    quality_summary: packageData.quality_summary ?? null,
    quality_signals: packageData.quality_signals ?? [],
    evidence_buckets: packageData.evidence_buckets ?? [],
    coverage_gaps: coverageSummariesFromPackage(packageData),
    concept_grounding: conceptGroundingSummariesFromPackage(packageData),
    diversity: retrievalDiversityReport(packageData),
  };
}
