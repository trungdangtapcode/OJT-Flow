import type {
  RetrievalHit,
  RetrievalRelevanceJudgment,
} from "../../../types";
import type { RetrievalRunComparison } from "./retrieval-run-comparison";
import type {
  RelevanceJudgment,
  RelevanceJudgmentIndex,
} from "./retrieval-judgment-types";

export function judgmentsForComparison(
  comparison: RetrievalRunComparison,
  judgments: RelevanceJudgmentIndex,
): RelevanceJudgment[] {
  const evidenceIds = new Set([
    ...comparison.addedEvidenceIds,
    ...comparison.removedEvidenceIds,
    ...comparison.retainedEvidenceIds,
  ]);
  return Object.values(judgments)
    .filter(
      (judgment) =>
        evidenceIds.has(judgment.evidenceId) &&
        (judgment.runId === comparison.activeRunId ||
          judgment.runId === comparison.baselineRunId),
    )
    .sort((left, right) => left.evidenceId.localeCompare(right.evidenceId));
}

export function relevanceJudgmentFromPersisted(
  judgment: RetrievalRelevanceJudgment,
  run: { query: string; runId: string; signature: string },
): RelevanceJudgment {
  return {
    evidenceId: judgment.evidence_id,
    judgedAt: judgment.updated_at,
    judgmentId: judgment.judgment_id,
    query: run.query,
    rating: judgment.rating,
    runId: run.runId,
    searchSignature: run.signature,
    sourceId: judgment.source_id ?? null,
    value: judgment.value,
  };
}

export function judgmentsForRunHits(
  runId: string,
  hits: RetrievalHit[],
  judgments: RelevanceJudgmentIndex,
): RelevanceJudgment[] {
  return hits
    .map((hit) => judgments[relevanceJudgmentKey(runId, hit.evidence.evidence_id)] ?? null)
    .filter((judgment): judgment is RelevanceJudgment => judgment !== null);
}

export function relevanceJudgmentKey(runId: string, evidenceId: string): string {
  return `${runId}:${evidenceId}`;
}
