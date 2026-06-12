import type * as React from "react";

import { apiErrorMessage } from "../../../lib/api-error-diagnostics";
import type { RetrievalActiveLearningStatus } from "../../../types";
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
  const activeLearningError = args.activeLearningCandidatesQuery.error
    ? apiErrorMessage(args.activeLearningCandidatesQuery.error)
    : null;

  return {
    activeEvaluation: args.workspace.judgmentSession.persistedJudgmentEvaluation,
    activeLearningCandidates: args.activeLearningCandidatesQuery.data ?? [],
    activeLearningSummary: args.activeLearningSummaryQuery.data ?? null,
    activeRun: args.workspace.runSession.activeRun,
    errorMessage: regressionJudgmentsError ?? regressionSummaryError ?? activeLearningError,
    formatCount,
    formatNullableDecimal,
    formatNullablePercent,
    formatPercent,
    globalJudgments: args.regressionJudgmentsQuery.data ?? [],
    globalSummary: args.regressionSummaryQuery.data ?? null,
    isLoading:
      args.regressionJudgmentsQuery.isLoading ||
      args.regressionSummaryQuery.isLoading ||
      args.activeLearningCandidatesQuery.isLoading,
    isRefreshing:
      args.regressionJudgmentsQuery.isFetching ||
      args.regressionSummaryQuery.isFetching ||
      args.activeLearningCandidatesQuery.isFetching,
    onRefresh: () => {
      void args.regressionJudgmentsQuery.refetch();
      void args.regressionSummaryQuery.refetch();
      void args.activeLearningCandidatesQuery.refetch();
      void args.activeLearningSummaryQuery.refetch();
    },
    onUpdateActiveLearningCandidate: (
      candidateId: string,
      status: RetrievalActiveLearningStatus,
    ) => {
      args.updateActiveLearningCandidateMutation.mutate({
        candidateId,
        payload: { status },
      });
    },
    searchRuns: args.workspace.runSession.searchRuns,
  };
}
