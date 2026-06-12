import type {
  RetrievalHit,
  RetrievalRecommendedAction,
} from "../../../types";
import {
  evidenceReportFromHitCardView,
} from "../model/hit-card-report";
import {
  type HitCardView,
} from "../model/hit-card-view-model";
import type { HitCardRelevanceJudgment } from "../components/hit-card-types";
import {
  copyTextToClipboard,
  useCopyFeedback,
} from "../components/copy-feedback";

export function useHitCardCopyReport({
  formatClaim,
  hit,
  judgment,
  recommendedActions,
  view,
}: {
  formatClaim: (claim: string) => string;
  hit: RetrievalHit;
  judgment: HitCardRelevanceJudgment;
  recommendedActions: RetrievalRecommendedAction[];
  view: HitCardView;
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const evidenceCopied = copiedKey === view.evidenceCopyKey;

  const copyEvidenceReport = async () => {
    await copyTextToClipboard(
      JSON.stringify(
        evidenceReportFromHitCardView({
          formatClaim,
          hit,
          judgment,
          recommendedActions,
          view,
        }),
        null,
        2,
      ),
    );
    markCopied(view.evidenceCopyKey);
  };

  return {
    copyEvidenceReport,
    evidenceCopied,
  };
}
