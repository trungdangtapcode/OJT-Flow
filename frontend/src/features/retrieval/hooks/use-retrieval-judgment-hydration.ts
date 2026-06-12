import * as React from "react";

import type { RetrievalRelevanceJudgment } from "../../../types";
import {
  relevanceJudgmentFromPersisted,
  relevanceJudgmentKey,
  type RelevanceJudgmentIndex,
} from "../model/retrieval-judgment-model";
import type { RetrievalSearchRun } from "../model/retrieval-run-summary";

export function usePruneRelevanceJudgments({
  searchRuns,
  setRelevanceJudgments,
}: {
  searchRuns: RetrievalSearchRun[];
  setRelevanceJudgments: React.Dispatch<React.SetStateAction<RelevanceJudgmentIndex>>;
}) {
  React.useEffect(() => {
    const runIds = new Set(searchRuns.map((run) => run.runId));
    setRelevanceJudgments((current) => {
      const next = Object.fromEntries(
        Object.entries(current).filter(([, judgment]) => runIds.has(judgment.runId)),
      );
      return Object.keys(next).length === Object.keys(current).length ? current : next;
    });
  }, [searchRuns, setRelevanceJudgments]);
}

export function useHydratePersistedRelevanceJudgments({
  activeRun,
  persistedJudgments,
  setRelevanceJudgments,
}: {
  activeRun: RetrievalSearchRun | null;
  persistedJudgments: RetrievalRelevanceJudgment[] | undefined;
  setRelevanceJudgments: React.Dispatch<React.SetStateAction<RelevanceJudgmentIndex>>;
}) {
  React.useEffect(() => {
    if (!activeRun || !persistedJudgments) return;
    const hitEvidenceIds = new Set(
      activeRun.packageData.hits.map((hit) => hit.evidence.evidence_id),
    );
    const matchingJudgments = persistedJudgments.filter((judgment) =>
      hitEvidenceIds.has(judgment.evidence_id),
    );
    if (!matchingJudgments.length) return;
    setRelevanceJudgments((current) => {
      const next = { ...current };
      for (const judgment of matchingJudgments) {
        const key = relevanceJudgmentKey(activeRun.runId, judgment.evidence_id);
        next[key] = relevanceJudgmentFromPersisted(judgment, {
          query: activeRun.payload.query,
          runId: activeRun.runId,
          signature: activeRun.signature,
        });
      }
      return next;
    });
  }, [activeRun, persistedJudgments, setRelevanceJudgments]);
}
