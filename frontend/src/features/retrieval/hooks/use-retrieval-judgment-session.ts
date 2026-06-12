import * as React from "react";

import type { RelevanceJudgmentIndex } from "../model/retrieval-judgment-model";
import type { RetrievalSearchRun } from "../model/retrieval-run-summary";
import { useRetrievalJudgmentActions } from "./use-retrieval-judgment-actions";
import {
  useHydratePersistedRelevanceJudgments,
  usePruneRelevanceJudgments,
} from "./use-retrieval-judgment-hydration";
import { useRetrievalJudgmentQueries } from "./use-retrieval-judgment-queries";

export function useRetrievalJudgmentSession({
  activeRun,
  searchRuns,
}: {
  activeRun: RetrievalSearchRun | null;
  searchRuns: RetrievalSearchRun[];
}) {
  const [relevanceJudgments, setRelevanceJudgments] =
    React.useState<RelevanceJudgmentIndex>({});
  const {
    persistedJudgmentEvaluationQuery,
    persistedJudgmentSummaryQuery,
    persistedJudgmentsQuery,
  } = useRetrievalJudgmentQueries(activeRun);
  const {
    deleteJudgmentMutation,
    setHitJudgment,
    upsertJudgmentMutation,
  } = useRetrievalJudgmentActions({
    relevanceJudgments,
    setRelevanceJudgments,
  });
  const isJudgmentSyncing = Boolean(
    activeRun &&
      (persistedJudgmentsQuery.isFetching ||
        persistedJudgmentSummaryQuery.isFetching ||
        persistedJudgmentEvaluationQuery.isFetching ||
        upsertJudgmentMutation.isPending ||
        deleteJudgmentMutation.isPending),
  );

  usePruneRelevanceJudgments({ searchRuns, setRelevanceJudgments });
  useHydratePersistedRelevanceJudgments({
    activeRun,
    persistedJudgments: persistedJudgmentsQuery.data,
    setRelevanceJudgments,
  });

  const clearRelevanceJudgments = () => {
    setRelevanceJudgments({});
  };

  return {
    clearRelevanceJudgments,
    isJudgmentSyncing,
    persistedJudgmentEvaluation: persistedJudgmentEvaluationQuery.data ?? null,
    persistedJudgmentSummary: persistedJudgmentSummaryQuery.data ?? null,
    relevanceJudgments,
    setHitJudgment,
  };
}
