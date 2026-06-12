import * as React from "react";

import {
  comparisonOperatorSummary,
  comparisonRecommendedActionSummary,
  comparisonReportFromComparison,
  comparisonReportRecommendedActions,
} from "../model/retrieval-comparison-diagnosis";
import { judgmentsForComparison } from "../model/retrieval-judgment-model";
import {
  comparisonRulePackChangeViews,
} from "../model/retrieval-run-comparison";
import { activeSearchRunComparison } from "../model/search-run-comparison-active";
import type { SearchRunHistoryPanelProps } from "./search-run-history-panel-types";

export function useSearchRunComparisonView({
  activeRunId,
  comparisonBaselineRunId,
  relevanceJudgments,
  runs,
}: Pick<
  SearchRunHistoryPanelProps,
  "activeRunId" | "comparisonBaselineRunId" | "relevanceJudgments" | "runs"
>) {
  const activeRunComparison = React.useMemo(() => {
    return activeSearchRunComparison({
      activeRunId,
      comparisonBaselineRunId,
      runs,
    });
  }, [activeRunId, comparisonBaselineRunId, runs]);

  const comparisonJudgments = React.useMemo(
    () =>
      activeRunComparison
        ? judgmentsForComparison(activeRunComparison, relevanceJudgments)
        : [],
    [activeRunComparison, relevanceJudgments],
  );
  const comparisonRecommendedActions = React.useMemo(
    () =>
      activeRunComparison
        ? comparisonReportRecommendedActions(activeRunComparison, comparisonJudgments)
        : [],
    [activeRunComparison, comparisonJudgments],
  );
  const comparisonActionSummary = React.useMemo(
    () => comparisonRecommendedActionSummary(comparisonRecommendedActions),
    [comparisonRecommendedActions],
  );
  const comparisonOperatorView = React.useMemo(
    () =>
      activeRunComparison
        ? comparisonOperatorSummary(activeRunComparison, comparisonRecommendedActions)
        : null,
    [activeRunComparison, comparisonRecommendedActions],
  );
  const comparisonReportJson = React.useMemo(
    () =>
      activeRunComparison
        ? JSON.stringify(
            comparisonReportFromComparison(
              activeRunComparison,
              comparisonJudgments,
              comparisonRecommendedActions,
            ),
            null,
            2,
          )
        : "",
    [activeRunComparison, comparisonJudgments, comparisonRecommendedActions],
  );
  const comparisonRulePackViews = React.useMemo(
    () =>
      activeRunComparison
        ? comparisonRulePackChangeViews(activeRunComparison.rulePackChanges)
        : [],
    [activeRunComparison],
  );

  return {
    comparisonActionSummary,
    comparisonOperatorView,
    comparisonRecommendedActions,
    comparisonReportJson,
    comparisonRulePackViews,
    activeRunComparison,
  };
}
