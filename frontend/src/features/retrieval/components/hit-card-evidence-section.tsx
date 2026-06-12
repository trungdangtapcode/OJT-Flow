import type { RetrievalHit } from "../../../types";
import {
  evidenceUseGuidance,
} from "../model/retrieval-evidence-model";
import type { HitCardView } from "../model/hit-card-view-model";
import {
  EvidenceUseGuidancePanel,
  EvidenceUsabilitySummaryPanel,
  HitMatchExplanationPanel,
} from "./evidence-interpretation-guidance";
import {
  EvidenceProvenanceSummary,
  SnippetBlock,
} from "./evidence-provenance-snippet";
import { HitEvidenceAuditStrip } from "./hit-evidence-audit-strip";
import type { RelevanceJudgmentValue } from "../model/retrieval-judgment-model";
import type { HitCardRelevanceJudgment } from "./hit-card-types";

export function HitCardEvidenceSection({
  formatClaim,
  formatCount,
  hit,
  judgment,
  judgmentLabel,
  view,
}: {
  formatClaim: (claim: string) => string;
  formatCount: (count: number, singular: string) => string;
  hit: RetrievalHit;
  judgment: HitCardRelevanceJudgment;
  judgmentLabel: (value: RelevanceJudgmentValue) => string;
  view: HitCardView;
}) {
  const evidence = hit.evidence;

  return (
    <>
      {hit.snippet ? (
        <SnippetBlock formatClaim={formatClaim} snippet={hit.snippet} />
      ) : null}

      <p className="break-words text-sm leading-6 text-muted-foreground">
        {formatClaim(evidence.claim)}
      </p>

      <HitEvidenceAuditStrip formatCount={formatCount} summary={view.supportSummary} />

      <EvidenceUsabilitySummaryPanel summary={view.usabilitySummary} />

      <EvidenceUseGuidancePanel
        guidance={evidenceUseGuidance({
          explanation: view.matchExplanation,
          judgment,
          judgmentLabel,
          summary: view.supportSummary,
        })}
      />

      <HitMatchExplanationPanel
        explanation={view.matchExplanation}
        formatCount={formatCount}
      />

      <EvidenceProvenanceSummary
        entries={view.provenanceEntries}
        formatCount={formatCount}
      />
    </>
  );
}
