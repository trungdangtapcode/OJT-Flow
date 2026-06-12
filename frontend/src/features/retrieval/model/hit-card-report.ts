import type {
  RetrievalHit,
  RetrievalRecommendedAction,
} from "../../../types";
import { evidenceReportFromHit } from "./retrieval-evidence-model";
import type { RetrievalEvidenceJudgment } from "./retrieval-evidence-types";
import type { HitCardView } from "./hit-card-view-model";

export function evidenceReportFromHitCardView({
  formatClaim,
  hit,
  judgment,
  recommendedActions,
  view,
}: {
  formatClaim: (claim: string) => string;
  hit: RetrievalHit;
  judgment: RetrievalEvidenceJudgment | null;
  recommendedActions: RetrievalRecommendedAction[];
  view: HitCardView;
}) {
  return evidenceReportFromHit({
    formatClaim,
    hit,
    judgment,
    matchExplanation: view.matchExplanation,
    provenanceEntries: view.provenanceEntries,
    recommendedActions,
    signals: view.hitSignals,
    supportSummary: view.supportSummary,
    usabilitySummary: view.usabilitySummary,
  });
}
