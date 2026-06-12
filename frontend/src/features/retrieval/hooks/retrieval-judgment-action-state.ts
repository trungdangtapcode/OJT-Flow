import type {
  RetrievalRelevanceJudgment,
} from "../../../types";
import {
  optimisticRelevanceJudgment,
  relevanceJudgmentFromPersisted,
  removeJudgmentFromIndex,
  setJudgmentInIndex,
  type RelevanceJudgment,
  type RelevanceJudgmentIndex,
  type SetHitJudgmentInput,
} from "../model/retrieval-judgment-model";

export function removeJudgmentActionState({
  current,
  key,
}: {
  current: RelevanceJudgmentIndex;
  key: string;
}) {
  return removeJudgmentFromIndex(current, key);
}

export function optimisticJudgmentActionState({
  current,
  existing,
  input,
  key,
}: {
  current: RelevanceJudgmentIndex;
  existing: RelevanceJudgment | null;
  input: SetHitJudgmentInput;
  key: string;
}) {
  return setJudgmentInIndex(
    current,
    key,
    optimisticRelevanceJudgment({
      ...input,
      existing,
    }),
  );
}

export function persistedJudgmentActionState({
  current,
  input,
  key,
  persisted,
}: {
  current: RelevanceJudgmentIndex;
  input: SetHitJudgmentInput;
  key: string;
  persisted: RetrievalRelevanceJudgment;
}) {
  if (current[key]?.value !== input.value) return current;
  return {
    ...current,
    [key]: relevanceJudgmentFromPersisted(persisted, {
      query: input.queryText,
      runId: input.runId,
      signature: input.searchSignature ?? "",
    }),
  };
}
