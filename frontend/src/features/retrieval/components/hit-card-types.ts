import type { RetrievalEvidenceJudgment } from "../model/retrieval-evidence-types";
import type {
  RetrievalEvidenceBucket,
  RetrievalHit,
  RetrievalRecommendedAction,
} from "../../../types";
import type { DiversitySelectionStack } from "../model/retrieval-source-diversity-types";
import type { RelevanceJudgmentValue } from "../model/retrieval-judgment-model";

export type HitCardRelevanceJudgment = RetrievalEvidenceJudgment | null;

export type HitCardProps = {
  diversitySelection: DiversitySelectionStack | null;
  evidenceBuckets: RetrievalEvidenceBucket[];
  formatClaim: (claim: string) => string;
  formatConfidence: (confidence: number | null | undefined) => string;
  formatCount: (count: number, singular: string) => string;
  formatScore: (score: number) => string;
  hit: RetrievalHit;
  index: number;
  judgment: HitCardRelevanceJudgment;
  judgmentLabel: (value: RelevanceJudgmentValue) => string;
  recommendedActions: RetrievalRecommendedAction[];
  onSetJudgment: (value: RelevanceJudgmentValue) => void;
};
