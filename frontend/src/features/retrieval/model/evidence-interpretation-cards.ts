import type {
  RetrievalEvidenceBucket,
  RetrievalHit,
  RetrievalPackage,
  RetrievalRecommendedAction,
} from "../../../types";
import type { EvidenceInterpretationCard } from "./evidence-interpretation-types";
import { coverageInterpretationCard } from "./evidence-interpretation-coverage-card";
import { nextActionInterpretationCard } from "./evidence-interpretation-next-action-card";
import { topMatchInterpretationCard } from "./evidence-interpretation-top-match-card";

export type EvidenceInterpretationCardContext = {
  backend: RetrievalPackage["interpretation"] | null;
  missingRequiredBuckets: RetrievalEvidenceBucket[];
  packageData: RetrievalPackage;
  primaryAction: RetrievalRecommendedAction | null;
  requiredBuckets: RetrievalEvidenceBucket[];
  topHit: RetrievalHit | null;
};

export function evidenceInterpretationCards({
  backend,
  missingRequiredBuckets,
  packageData,
  primaryAction,
  requiredBuckets,
  topHit,
}: EvidenceInterpretationCardContext): EvidenceInterpretationCard[] {
  return [
    topMatchInterpretationCard({ backend, topHit }),
    coverageInterpretationCard({
      backend,
      missingRequiredBuckets,
      packageData,
      requiredBuckets,
    }),
    nextActionInterpretationCard({ backend, primaryAction }),
  ];
}
