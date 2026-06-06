import { CheckCircle2, Clipboard, Gauge } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { humanize } from "../../../lib/utils";
import type {
  RetrievalEvidenceBucket,
  RetrievalHit,
  RetrievalRecommendedAction,
} from "../../../types";
import {
  evidenceReportFromHit,
  evidenceSignalsFromHit,
  evidenceSupportSummary,
  evidenceUsabilitySummary,
  evidenceUseGuidance,
  hitMatchExplanation,
  provenanceEntriesFromEvidence,
} from "../model/retrieval-evidence-model";
import type { DiversitySelectionStack } from "./source-diversity-panel";
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
import {
  ConceptMatchExplanation,
  DiversitySelectionExplanation,
  QueryAspectMatchExplanation,
  ScoreExplanation,
  ScoreMeter,
} from "./hit-explanation-panels";
import {
  RelevanceJudgmentControl,
  type RelevanceJudgmentValue,
} from "./relevance-judgment-control";
import {
  copyTextToClipboard,
  useCopyFeedback,
} from "./copy-feedback";

type RelevanceJudgment = {
  value: RelevanceJudgmentValue;
} | null;

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
}: {
  diversitySelection: DiversitySelectionStack | null;
  evidenceBuckets: RetrievalEvidenceBucket[];
  formatClaim: (claim: string) => string;
  formatConfidence: (confidence: number | null | undefined) => string;
  formatCount: (count: number, singular: string) => string;
  formatScore: (score: number) => string;
  hit: RetrievalHit;
  index: number;
  judgment: RelevanceJudgment;
  judgmentLabel: (value: RelevanceJudgmentValue) => string;
  recommendedActions: RetrievalRecommendedAction[];
  onSetJudgment: (value: RelevanceJudgmentValue) => void;
}) {
  const evidence = hit.evidence;
  const provenanceEntries = provenanceEntriesFromEvidence(evidence);
  const hitSignals = evidenceSignalsFromHit(hit);
  const supportSummary = evidenceSupportSummary({
    hit,
    provenanceEntries,
    signals: hitSignals,
  });
  const matchExplanation = hitMatchExplanation({
    buckets: evidenceBuckets,
    hit,
    provenanceEntries,
    signals: hitSignals,
  });
  const usabilitySummary = evidenceUsabilitySummary({
    explanation: matchExplanation,
    formatCount,
    judgment,
    judgmentLabel,
    summary: supportSummary,
  });
  const { copiedKey, markCopied } = useCopyFeedback();
  const evidenceCopyKey = `evidence-report-${evidence.source_id}-${index}`;
  const evidenceCopied = copiedKey === evidenceCopyKey;

  const copyEvidenceReport = async () => {
    await copyTextToClipboard(
      JSON.stringify(
        evidenceReportFromHit({
          formatClaim,
          hit,
          judgment,
          matchExplanation,
          provenanceEntries,
          recommendedActions,
          signals: hitSignals,
          supportSummary,
          usabilitySummary,
        }),
        null,
        2,
      ),
    );
    markCopied(evidenceCopyKey);
  };

  return (
    <article className="grid min-w-0 gap-3 rounded-md border border-border bg-card p-3 shadow-sm">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs font-bold uppercase text-muted-foreground">Rank {index + 1}</div>
          <h3 className="mt-1 break-words text-base font-extrabold leading-5">
            {evidence.source_id}
          </h3>
          <div className="mt-1 flex flex-wrap gap-1.5 text-xs font-bold text-muted-foreground">
            <span>{humanize(evidence.source_type)}</span>
            <span>/</span>
            <span>{humanize(evidence.trust_level)}</span>
            {String(evidence.locator.standard_system ?? "") ? (
              <>
                <span>/</span>
                <span>{String(evidence.locator.standard_system)}</span>
              </>
            ) : null}
          </div>
        </div>
        <div className="flex flex-wrap justify-end gap-1.5">
          <Badge variant="success">{formatConfidence(evidence.confidence)}</Badge>
          <Badge variant="muted">score {formatScore(hit.score)}</Badge>
          <Button
            aria-label={`Copy evidence report for ${evidence.source_id}`}
            onClick={() => void copyEvidenceReport()}
            size="sm"
            type="button"
            variant="outline"
          >
            {evidenceCopied ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <Clipboard className="h-4 w-4" />
            )}
            {evidenceCopied ? "Copied" : "Copy evidence JSON"}
          </Button>
          <HelpTooltip label="Evidence JSON report help">
            Copies this evidence hit with identity, score details, provenance, match explanation, bucket support, locators, and snippet context.
          </HelpTooltip>
        </div>
      </div>

      {hit.snippet ? (
        <SnippetBlock formatClaim={formatClaim} snippet={hit.snippet} />
      ) : null}

      <p className="break-words text-sm leading-6 text-muted-foreground">
        {formatClaim(evidence.claim)}
      </p>

      <HitEvidenceAuditStrip formatCount={formatCount} summary={supportSummary} />

      <EvidenceUsabilitySummaryPanel summary={usabilitySummary} />

      <EvidenceUseGuidancePanel
        guidance={evidenceUseGuidance({
          explanation: matchExplanation,
          judgment,
          judgmentLabel,
          summary: supportSummary,
        })}
      />

      <HitMatchExplanationPanel explanation={matchExplanation} formatCount={formatCount} />

      <EvidenceProvenanceSummary
        entries={provenanceEntries}
        formatCount={formatCount}
      />

      <RelevanceJudgmentControl
        judgment={judgment}
        onSetJudgment={onSetJudgment}
      />

      <div className="grid gap-2 md:grid-cols-3">
        <ScoreMeter formatScore={formatScore} label="Lexical" value={hit.lexical_score} />
        <ScoreMeter formatScore={formatScore} label="Vector" value={hit.vector_score} />
        <ScoreMeter formatScore={formatScore} label="Rerank" value={hit.rerank_score} />
      </div>

      <ScoreExplanation components={hitSignals.scoreComponents} formatScore={formatScore} />

      <DiversitySelectionExplanation
        formatScore={formatScore}
        selection={diversitySelection}
      />

      <ConceptMatchExplanation matches={hitSignals.conceptMatches} />

      <QueryAspectMatchExplanation matches={hitSignals.queryAspectMatches} />

      {hitSignals.rankingBoostSignals.length ? (
        <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
          <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
            <Gauge className="h-3.5 w-3.5 shrink-0" />
            <span>Ranking signals</span>
          </div>
          <div className="grid gap-1.5">
            {hitSignals.rankingBoostSignals.map((signal) => (
              <div
                className="flex min-w-0 flex-wrap items-center gap-1.5 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs"
                key={signal.ruleId}
              >
                <Badge className="max-w-full break-words" variant="muted">
                  {signal.label}
                </Badge>
                {signal.weight !== null ? (
                  <span className="font-mono font-semibold text-muted-foreground">
                    +{formatScore(signal.weight)}
                  </span>
                ) : null}
                <span className="min-w-0 flex-1 break-words font-semibold text-muted-foreground">
                  {signal.reason}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-wrap gap-1.5">
        {hit.matched_terms.slice(0, 12).map((term) => (
          <span
            className="max-w-full break-words rounded-full bg-muted px-2 py-1 text-xs font-bold text-muted-foreground"
            key={term}
          >
            {term}
          </span>
        ))}
        {!hit.matched_terms.length ? (
          <span className="text-xs font-semibold text-muted-foreground">No exact terms matched.</span>
        ) : null}
      </div>

      <details className="rounded-md border border-border bg-muted/20 p-2 text-xs">
        <summary className="cursor-pointer font-bold">Locator and evidence ID</summary>
        <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words font-mono">
          {JSON.stringify(
            {
              evidence_id: evidence.evidence_id,
              locator: evidence.locator,
              source_locator: hit.source_locator,
            },
            null,
            2,
          )}
        </pre>
      </details>
    </article>
  );
}
