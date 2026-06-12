import { relevanceJudgmentRating } from "./retrieval-judgment-labels";
import {
  relevanceJudgmentKey,
} from "./retrieval-judgment-mapping";
import type {
  RelevanceJudgment,
  RelevanceJudgmentIndex,
  RelevanceJudgmentValue,
  SetHitJudgmentInput,
} from "./retrieval-judgment-types";

export function shouldToggleOffJudgment(
  existing: RelevanceJudgment | null,
  value: RelevanceJudgmentValue,
): boolean {
  return existing?.value === value;
}

export function removeJudgmentFromIndex(
  judgments: RelevanceJudgmentIndex,
  key: string,
): RelevanceJudgmentIndex {
  const { [key]: _removed, ...remaining } = judgments;
  return remaining;
}

export function optimisticRelevanceJudgment({
  evidence,
  queryText,
  runId,
  searchSignature,
  value,
  existing,
}: SetHitJudgmentInput & {
  existing: RelevanceJudgment | null;
}): RelevanceJudgment {
  return {
    evidenceId: evidence.evidence_id,
    judgedAt: new Date().toISOString(),
    judgmentId: existing?.judgmentId ?? null,
    query: queryText,
    rating: relevanceJudgmentRating(value),
    runId,
    searchSignature,
    sourceId: evidence.source_id,
    value,
  };
}

export function setJudgmentInIndex(
  judgments: RelevanceJudgmentIndex,
  key: string,
  judgment: RelevanceJudgment,
): RelevanceJudgmentIndex {
  return {
    ...judgments,
    [key]: judgment,
  };
}

export { relevanceJudgmentKey };
