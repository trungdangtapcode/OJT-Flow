import * as React from "react";

import type {
  RetrievalPackage,
  RetrievalPlan,
  RetrievalSearchPayload,
} from "../../../types";
import { copyTextToClipboard } from "./copy-feedback";
import { searchPlanPreviewReportText } from "./search-plan-preview-report";
import { searchPlanPreviewView } from "./search-plan-preview-panel-view";

export function useSearchPlanPreviewPanelView({
  currentPlanData,
  currentPlanPayload,
  packageData,
  submittedSearchPayload,
}: {
  currentPlanData: RetrievalPlan | undefined;
  currentPlanPayload: RetrievalSearchPayload | null;
  packageData: RetrievalPackage | undefined;
  submittedSearchPayload: RetrievalSearchPayload | null;
}) {
  const view = React.useMemo(
    () => searchPlanPreviewView({ currentPlanData, packageData }),
    [currentPlanData, packageData],
  );
  const copyPlan = React.useCallback(async () => {
    await copyTextToClipboard(
      searchPlanPreviewReportText({
        currentPlanData,
        currentPlanPayload,
        packageData,
        submittedSearchPayload,
      }),
    );
  }, [currentPlanData, currentPlanPayload, packageData, submittedSearchPayload]);

  return { copyPlan, view };
}
