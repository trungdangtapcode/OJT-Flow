import type {
  RetrievalPackage,
  RetrievalPlan,
  RetrievalSearchPayload,
} from "../../../types";
import {
  retrievalSearchPlanPreviewReport,
} from "../model/retrieval-report-model";

export function searchPlanPreviewReportText({
  currentPlanData,
  currentPlanPayload,
  packageData,
  submittedSearchPayload,
}: {
  currentPlanData: RetrievalPlan | undefined;
  currentPlanPayload: RetrievalSearchPayload | null;
  packageData: RetrievalPackage | undefined;
  submittedSearchPayload: RetrievalSearchPayload | null;
}): string {
  return JSON.stringify(
    retrievalSearchPlanPreviewReport(
      packageData,
      packageData ? submittedSearchPayload : currentPlanPayload,
      currentPlanData,
    ),
    null,
    2,
  );
}
