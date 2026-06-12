import type {
  RetrievalPackage,
  RetrievalSearchPayload,
} from "../../../types";
import {
  evidenceSupportMatrixRows,
  evidenceSupportSummaryForHit,
} from "./retrieval-evidence-model";
import { optionalStringValue } from "./retrieval-evidence-utils";
import {
  activeFacetFiltersFromPayload,
  activeFilterEntries,
  type ActiveFacetFilters,
} from "./retrieval-filter-model";
import {
  formatConfidence,
} from "./retrieval-format";
import {
  judgmentsForRunHits,
  relevanceJudgmentMetrics,
  type RelevanceJudgmentIndex,
} from "./retrieval-judgment-model";
import { retrievalSearchCockpitView } from "./retrieval-cockpit-view-model";
import { retrievalCockpitReportFromPackage } from "./retrieval-report-model";

export function searchResultsViewModel({
  activeFilters,
  packageData,
  relevanceJudgments,
  runId,
  submittedSearchPayload,
}: {
  activeFilters: ActiveFacetFilters;
  packageData: RetrievalPackage;
  relevanceJudgments: RelevanceJudgmentIndex;
  runId: string | null;
  submittedSearchPayload: RetrievalSearchPayload | null;
}) {
  const resultFilters = submittedSearchPayload
    ? activeFacetFiltersFromPayload(submittedSearchPayload)
    : activeFilters;
  const resultFilterEntries = activeFilterEntries(resultFilters);
  const runJudgments = runId
    ? judgmentsForRunHits(runId, packageData.hits, relevanceJudgments)
    : [];
  const judgmentMetrics = relevanceJudgmentMetrics(packageData.hits, runJudgments);
  const requiredBuckets = (packageData.evidence_buckets ?? []).filter(
    (bucket) => bucket.required,
  );
  const cockpitView = retrievalSearchCockpitView(packageData, submittedSearchPayload);

  return {
    cockpitReportJson: JSON.stringify(
      retrievalCockpitReportFromPackage(packageData, submittedSearchPayload),
      null,
      2,
    ),
    cockpitView,
    coveredRequiredBucketCount: requiredBuckets.filter((bucket) => bucket.hit_count > 0)
      .length,
    judgmentMetrics,
    requiredBucketCount: requiredBuckets.length,
    resultFilterEntries,
    resultFilters,
    supportMatrixRows: evidenceSupportMatrixRows({
      formatConfidence,
      packageData,
      relevanceJudgments,
      runId,
      standardSystemValue: optionalStringValue,
      summaryForHit: evidenceSupportSummaryForHit,
    }),
  };
}
