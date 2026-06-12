import { useHitCardCopyReport } from "../hooks/use-hit-card-copy-report";
import { evidenceAnchorId } from "../../../lib/evidence-links";
import { hitCardViewModel } from "../model/hit-card-view-model";
import { HitCardEvidenceSection } from "./hit-card-evidence-section";
import { RelevanceJudgmentControl } from "./relevance-judgment-control";
import { HitCardHeader } from "./hit-card-header";
import { HitCardScoreSection } from "./hit-card-score-section";
import type { HitCardProps } from "./hit-card-types";
import { HitLocatorDetails } from "./hit-locator-details";

export function HitCard({
  diversitySelection,
  evidenceBuckets,
  formatClaim,
  formatConfidence,
  formatCount,
  formatScore,
  hit,
  index,
  judgment,
  judgmentLabel,
  recommendedActions,
  onSetJudgment,
}: HitCardProps) {
  const evidence = hit.evidence;
  const view = hitCardViewModel({
    evidenceBuckets,
    formatCount,
    hit,
    index,
    judgment,
    judgmentLabel,
  });
  const { copyEvidenceReport, evidenceCopied } = useHitCardCopyReport({
    formatClaim,
    hit,
    judgment,
    recommendedActions,
    view,
  });

  return (
    <article
      className="grid min-w-0 scroll-mt-24 gap-3 rounded-md border border-border bg-card p-3 shadow-sm"
      id={evidenceAnchorId(evidence.evidence_id)}
    >
      <HitCardHeader
        evidence={evidence}
        evidenceCopied={evidenceCopied}
        formatConfidence={formatConfidence}
        formatScore={formatScore}
        index={index}
        onCopyEvidenceReport={() => void copyEvidenceReport()}
        score={hit.score}
      />

      <HitCardEvidenceSection
        formatClaim={formatClaim}
        formatCount={formatCount}
        hit={hit}
        judgment={judgment}
        judgmentLabel={judgmentLabel}
        view={view}
      />

      <RelevanceJudgmentControl
        judgment={judgment}
        onSetJudgment={onSetJudgment}
      />

      <HitCardScoreSection
        diversitySelection={diversitySelection}
        formatScore={formatScore}
        hit={hit}
        view={view}
      />

      <HitLocatorDetails evidence={evidence} sourceLocator={hit.source_locator} />
    </article>
  );
}
