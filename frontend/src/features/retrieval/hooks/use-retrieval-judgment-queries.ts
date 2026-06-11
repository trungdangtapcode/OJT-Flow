import * as React from "react";

import {
  useRetrievalJudgmentEvaluationQuery,
  useRetrievalJudgmentSummaryQuery,
  useRetrievalJudgmentsQuery,
} from "../../../lib/server-state";
import type { RetrievalSearchRun } from "../model/retrieval-run-summary";

export function useRetrievalJudgmentQueries(activeRun: RetrievalSearchRun | null) {
  const persistedJudgmentsQuery = useRetrievalJudgmentsQuery({
    query: activeRun?.payload.query ?? null,
    limit: 500,
  });
  const persistedJudgmentSummaryQuery = useRetrievalJudgmentSummaryQuery({
    query: activeRun?.payload.query ?? null,
    limit: 1000,
  });
  const activeRunEvidenceIds = React.useMemo(
    () => activeRun?.packageData.hits.map((hit) => hit.evidence.evidence_id) ?? [],
    [activeRun],
  );
  const persistedJudgmentEvaluationQuery = useRetrievalJudgmentEvaluationQuery(
    activeRun
      ? {
          query: activeRun.payload.query,
          ranked_evidence_ids: activeRunEvidenceIds,
          cutoff: activeRun.packageData.hits.length,
        }
      : null,
  );

  return {
    persistedJudgmentEvaluationQuery,
    persistedJudgmentSummaryQuery,
    persistedJudgmentsQuery,
  };
}
