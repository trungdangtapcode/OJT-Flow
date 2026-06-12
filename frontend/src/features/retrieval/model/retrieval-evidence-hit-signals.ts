import type { RetrievalHit } from "../../../types";
import type { EvidenceHitSignals } from "./retrieval-evidence-types";
import { scoreComponentsFromHit } from "./retrieval-evidence-score-components";
import {
  conceptMatchesFromHit,
  queryAspectMatchesFromHit,
  rankingBoostSignalsFromHit,
} from "./retrieval-evidence-signal-extraction";

export function evidenceSignalsFromHit(hit: RetrievalHit): EvidenceHitSignals {
  return {
    conceptMatches: conceptMatchesFromHit(hit),
    queryAspectMatches: queryAspectMatchesFromHit(hit),
    rankingBoostSignals: rankingBoostSignalsFromHit(hit),
    scoreComponents: scoreComponentsFromHit(hit),
  };
}
