import type { RetrievalHit } from "../../../types";
import type { HitCardView } from "../model/hit-card-view-model";
import type { DiversitySelectionStack } from "../model/retrieval-source-diversity-types";
import {
  ConceptMatchExplanation,
  DiversitySelectionExplanation,
  QueryAspectMatchExplanation,
  ScoreExplanation,
  ScoreMeter,
} from "./hit-explanation-panels";
import { HitMatchedTerms } from "./hit-matched-terms";
import { HitRankingSignals } from "./hit-ranking-signals";

export function HitCardScoreSection({
  diversitySelection,
  formatScore,
  hit,
  view,
}: {
  diversitySelection: DiversitySelectionStack | null;
  formatScore: (score: number) => string;
  hit: RetrievalHit;
  view: HitCardView;
}) {
  return (
    <>
      <div className="grid gap-2 md:grid-cols-3">
        <ScoreMeter formatScore={formatScore} label="Lexical" value={hit.lexical_score} />
        <ScoreMeter formatScore={formatScore} label="Vector" value={hit.vector_score} />
        <ScoreMeter formatScore={formatScore} label="Rerank" value={hit.rerank_score} />
      </div>

      <ScoreExplanation components={view.hitSignals.scoreComponents} formatScore={formatScore} />

      <DiversitySelectionExplanation
        formatScore={formatScore}
        selection={diversitySelection}
      />

      <ConceptMatchExplanation matches={view.hitSignals.conceptMatches} />

      <QueryAspectMatchExplanation matches={view.hitSignals.queryAspectMatches} />

      <HitRankingSignals
        formatScore={formatScore}
        signals={view.hitSignals.rankingBoostSignals}
      />

      <HitMatchedTerms terms={hit.matched_terms} />
    </>
  );
}
