import type * as React from "react";

import { apiErrorMessage } from "../../../lib/api-error-diagnostics";
import type { RetrievalRegressionDashboard } from "../components/retrieval-regression-dashboard";
import {
  formatCount,
  formatNullableDecimal,
  formatNullablePercent,
  formatPercent,
} from "./retrieval-format";
import type { RetrievalPagePropsArgs } from "./retrieval-page-prop-types";

export function retrievalPageRegressionDashboardProps(
  args: RetrievalPagePropsArgs,
): React.ComponentProps<typeof RetrievalRegressionDashboard> {
  const regressionJudgmentsError = args.regressionJudgmentsQuery.error
    ? apiErrorMessage(args.regressionJudgmentsQuery.error)
    : null;
  const regressionSummaryError = args.regressionSummaryQuery.error
    ? apiErrorMessage(args.regressionSummaryQuery.error)
    : null;

  return {
    activeEvaluation: args.workspace.judgmentSession.persistedJudgmentEvaluation,
    activeRun: args.workspace.runSession.activeRun,
    errorMessage: regressionJudgmentsError ?? regressionSummaryError,
    formatCount,
    formatNullableDecimal,
    formatNullablePercent,
    formatPercent,
    globalJudgments: args.regressionJudgmentsQuery.data ?? [],
    globalSummary: args.regressionSummaryQuery.data ?? null,
    isLoading:
      args.regressionJudgmentsQuery.isLoading || args.regressionSummaryQuery.isLoading,
    isRefreshing:
      args.regressionJudgmentsQuery.isFetching || args.regressionSummaryQuery.isFetching,
    onRefresh: () => {
      void args.regressionJudgmentsQuery.refetch();
      void args.regressionSummaryQuery.refetch();
    },
    searchRuns: args.workspace.runSession.searchRuns,
  };
}
