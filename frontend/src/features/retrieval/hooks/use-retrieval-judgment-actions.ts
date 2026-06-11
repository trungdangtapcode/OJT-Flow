import * as React from "react";

import {
  useDeleteRetrievalJudgmentMutation,
  useRetrievalJudgmentMutation,
} from "../../../lib/server-state";
import type { Evidence } from "../../../types";
import {
  relevanceJudgmentKey,
  retrievalJudgmentPayload,
  shouldToggleOffJudgment,
  type RelevanceJudgmentIndex,
  type RelevanceJudgmentValue,
} from "../model/retrieval-judgment-model";
import {
  optimisticJudgmentActionState,
  persistedJudgmentActionState,
  removeJudgmentActionState,
} from "./retrieval-judgment-action-state";

export function useRetrievalJudgmentActions({
  relevanceJudgments,
  setRelevanceJudgments,
}: {
  relevanceJudgments: RelevanceJudgmentIndex;
  setRelevanceJudgments: React.Dispatch<React.SetStateAction<RelevanceJudgmentIndex>>;
}) {
  const upsertJudgmentMutation = useRetrievalJudgmentMutation();
  const deleteJudgmentMutation = useDeleteRetrievalJudgmentMutation();

  const setHitJudgment = (
    runId: string | null,
    queryText: string,
    searchSignature: string | null,
    evidence: Evidence,
    value: RelevanceJudgmentValue,
  ) => {
    if (!runId) return;
    const evidenceId = evidence.evidence_id;
    const key = relevanceJudgmentKey(runId, evidenceId);
    const existing = relevanceJudgments[key] ?? null;
    if (shouldToggleOffJudgment(existing, value)) {
      setRelevanceJudgments((current) => {
        return removeJudgmentActionState({ current, key });
      });
      if (existing.judgmentId) {
        deleteJudgmentMutation.mutate(existing.judgmentId);
      }
      return;
    }
    const judgmentInput = {
      evidence,
      queryText,
      runId,
      searchSignature,
      value,
    };
    setRelevanceJudgments((current) => {
      return optimisticJudgmentActionState({
        current,
        existing,
        input: judgmentInput,
        key,
      });
    });
    upsertJudgmentMutation.mutate(
      retrievalJudgmentPayload(judgmentInput),
      {
        onSuccess: (persisted) => {
          setRelevanceJudgments((current) => {
            return persistedJudgmentActionState({
              current,
              input: judgmentInput,
              key,
              persisted,
            });
          });
        },
      },
    );
  };

  return {
    deleteJudgmentMutation,
    setHitJudgment,
    upsertJudgmentMutation,
  };
}
