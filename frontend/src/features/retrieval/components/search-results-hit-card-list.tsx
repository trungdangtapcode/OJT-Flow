import type { Evidence, RetrievalPackage } from "../../../types";
import {
  formatClaim,
  formatConfidence,
  formatCount,
  formatScore,
} from "../model/retrieval-format";
import {
  judgmentLabel,
  relevanceJudgmentKey,
  type RelevanceJudgmentIndex,
  type RelevanceJudgmentValue,
} from "../model/retrieval-judgment-model";
import { diversitySelectionByEvidenceId } from "../model/retrieval-runtime-stack";
import { HitCard } from "./hit-card";

export function SearchResultsHitCardList({
  onSetJudgment,
  packageData,
  relevanceJudgments,
  runId,
}: {
  onSetJudgment: (evidence: Evidence, value: RelevanceJudgmentValue) => void;
  packageData: RetrievalPackage;
  relevanceJudgments: RelevanceJudgmentIndex;
  runId: string | null;
}) {
  const diversitySelections = diversitySelectionByEvidenceId(packageData);
  return (
    <>
      {packageData.hits.map((hit, index) => (
        <HitCard
          diversitySelection={diversitySelections.get(hit.evidence.evidence_id) ?? null}
          evidenceBuckets={packageData.evidence_buckets ?? []}
          formatClaim={formatClaim}
          formatConfidence={formatConfidence}
          formatCount={formatCount}
          formatScore={formatScore}
          hit={hit}
          index={index}
          judgment={
            runId
              ? relevanceJudgments[
                  relevanceJudgmentKey(runId, hit.evidence.evidence_id)
                ] ?? null
              : null
          }
          judgmentLabel={judgmentLabel}
          key={hit.evidence.evidence_id}
          onSetJudgment={(value) => onSetJudgment(hit.evidence, value)}
          recommendedActions={packageData.recommended_actions ?? []}
        />
      ))}
    </>
  );
}
