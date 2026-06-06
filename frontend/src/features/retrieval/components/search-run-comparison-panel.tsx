import { useEffect, useState } from "react";
import { CheckCircle2, Clipboard } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import {
  RunComparisonAtAGlance,
  RunComparisonDiagnosis,
  RunComparisonMetric,
  RunComparisonMetrics,
  RunComparisonOperatorSummary,
  RunComparisonRecommendedActions,
  type RunComparisonAtAGlanceView,
  type RunComparisonDiagnosisView,
  type RunComparisonMetricsView,
  type RunComparisonOperatorSummaryView,
  type RunComparisonRecommendedActionSummaryView,
  type RunComparisonRecommendedActionView,
} from "./run-comparison-summary-panels";
import {
  RunComparisonConceptGrounding,
  RunComparisonCoverage,
  RunComparisonEvidenceChange,
  RunComparisonFacetCoverage,
  RunComparisonQualitySignals,
  RunComparisonQueryAspects,
  RunComparisonQueryProfile,
  RunComparisonRankChanges,
  RunComparisonRulePacks,
  type RetrievalConceptGroundingComparisonView,
  type RetrievalCoverageComparisonView,
  type RetrievalFacetComparisonView,
  type RetrievalQualitySignalComparisonView,
  type RetrievalQueryAspectComparisonView,
  type RetrievalRankChangeView,
  type RetrievalRulePackChangeView,
  type RunComparisonQueryProfileView,
} from "./run-comparison-detail-panels";
import {
  RunComparisonSourceDiversity,
  type RetrievalSourceDiversityComparisonView,
} from "./source-diversity-panel";
import { SectionHelpText } from "./section-help-text";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export type SearchRunComparisonPanelView = RunComparisonAtAGlanceView &
  RunComparisonQueryProfileView & {
    addedEvidenceIds: string[];
    baselineQuery: string;
    candidateDelta: number;
    conceptGroundingComparison: RetrievalConceptGroundingComparisonView;
    coverageComparison: RetrievalCoverageComparisonView;
    diagnosis: RunComparisonDiagnosisView[];
    facetComparisons: RetrievalFacetComparisonView[];
    hitDelta: number;
    metrics: RunComparisonMetricsView;
    queryAspectComparison: RetrievalQueryAspectComparisonView;
    qualitySignalComparison: RetrievalQualitySignalComparisonView;
    qualityWarningDelta: number;
    rankChanges: RetrievalRankChangeView[];
    removedEvidenceIds: string[];
    retainedEvidenceIds: string[];
    rulePackChanged: boolean;
    sourceDiversityComparison: RetrievalSourceDiversityComparisonView;
    topSourceAfter: string | null;
    topSourceBefore: string | null;
    warningDelta: number;
  };

export function SearchRunComparisonPanel({
  actionSummary,
  comparison,
  copyTextToClipboard,
  deltaBadgeVariant,
  formatCount,
  formatDecimal,
  formatPercent,
  formatSignedDelta,
  operatorSummary,
  readinessLabel,
  recommendedActions,
  reportJson,
  rulePackChanges,
}: {
  actionSummary: RunComparisonRecommendedActionSummaryView;
  comparison: SearchRunComparisonPanelView;
  copyTextToClipboard: (text: string) => Promise<void>;
  deltaBadgeVariant: (delta: number, positiveIsGood: boolean) => BadgeVariant;
  formatCount: (count: number, singular: string) => string;
  formatDecimal: (value: number) => string;
  formatPercent: (value: number) => string;
  formatSignedDelta: (delta: number) => string;
  operatorSummary: RunComparisonOperatorSummaryView;
  readinessLabel: string;
  recommendedActions: RunComparisonRecommendedActionView[];
  reportJson: string;
  rulePackChanges: RetrievalRulePackChangeView[];
}) {
  const [reportCopied, setReportCopied] = useState(false);

  useEffect(() => {
    if (!reportCopied) return undefined;
    const timeoutId = window.setTimeout(() => setReportCopied(false), 1800);
    return () => window.clearTimeout(timeoutId);
  }, [reportCopied]);

  const copyReport = async () => {
    await copyTextToClipboard(reportJson);
    setReportCopied(true);
  };

  return (
    <div
      aria-label="Search run comparison"
      className="mt-1 grid gap-3 rounded-md border border-border bg-muted/25 p-3 text-sm"
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
          Run comparison
          <HelpTooltip label="Run comparison help">
            Compares the currently displayed search package against the selected baseline run. Use this to tune query scope, filters, and retrieval policy, not to make clinical conclusions.
          </HelpTooltip>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={comparison.topSourceChanged ? "warning" : "success"}>
            {comparison.topSourceChanged ? "top source changed" : "top source stable"}
          </Badge>
          <Badge variant={comparison.queryProfileChanged ? "warning" : "success"}>
            {comparison.queryProfileChanged ? "profile changed" : "profile stable"}
          </Badge>
          <Badge variant={comparison.rulePackChanged ? "warning" : "success"}>
            {comparison.rulePackChanged ? "rule packs changed" : "rule packs stable"}
          </Badge>
          <Badge variant={comparison.qualitySummaryChanged ? "warning" : "success"}>
            {comparison.qualitySummaryChanged ? "quality changed" : "quality stable"}
          </Badge>
          <Button
            aria-label="Copy retrieval comparison report"
            onClick={() => void copyReport()}
            size="sm"
            type="button"
            variant="outline"
          >
            {reportCopied ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <Clipboard className="h-4 w-4" />
            )}
            {reportCopied ? "Copied" : "Copy comparison JSON"}
          </Button>
          <HelpTooltip label="Comparison JSON report help">
            Copies active versus baseline search payloads, quality deltas, evidence changes, rank movement, and recommended tuning actions for offline review.
          </HelpTooltip>
        </div>
      </div>
      <SectionHelpText>
        Baseline is the older comparison run; active is the currently displayed package. Treat warning deltas, quality changes, and rank movement as tuning signals that need evidence review.
      </SectionHelpText>
      <RunComparisonOperatorSummary summary={operatorSummary} />
      <div className="grid gap-1 rounded-md border border-border bg-card px-3 py-2 text-xs">
        <span className="font-bold uppercase text-muted-foreground">Baseline query</span>
        <span className="break-words leading-5">{comparison.baselineQuery}</span>
      </div>
      <RunComparisonAtAGlance
        actionSummary={actionSummary}
        comparison={comparison}
        formatPercent={formatPercent}
        formatSignedDelta={formatSignedDelta}
        readinessLabel={readinessLabel}
      />
      <RunComparisonDiagnosis diagnosis={comparison.diagnosis} formatCount={formatCount} />
      <RunComparisonRecommendedActions
        actions={recommendedActions}
        actionSummary={actionSummary}
        formatCount={formatCount}
      />
      <RunComparisonMetrics
        formatDecimal={formatDecimal}
        formatPercent={formatPercent}
        metrics={comparison.metrics}
      />
      <RunComparisonSourceDiversity
        comparison={comparison.sourceDiversityComparison}
        formatPercent={formatPercent}
        formatSignedDelta={formatSignedDelta}
      />
      <div className="grid gap-2 sm:grid-cols-2">
        <RunComparisonMetric
          delta={comparison.hitDelta}
          deltaBadgeVariant={deltaBadgeVariant}
          formatSignedDelta={formatSignedDelta}
          label="Hits"
          positiveIsGood
        />
        <RunComparisonMetric
          delta={comparison.candidateDelta}
          deltaBadgeVariant={deltaBadgeVariant}
          formatSignedDelta={formatSignedDelta}
          label="Candidates"
          positiveIsGood
        />
        <RunComparisonMetric
          delta={comparison.warningDelta}
          deltaBadgeVariant={deltaBadgeVariant}
          formatSignedDelta={formatSignedDelta}
          label="Warnings"
          positiveIsGood={false}
        />
        <RunComparisonMetric
          delta={comparison.qualityWarningDelta}
          deltaBadgeVariant={deltaBadgeVariant}
          formatSignedDelta={formatSignedDelta}
          label="Quality issues"
          positiveIsGood={false}
        />
      </div>
      <div className="grid gap-2">
        <RunComparisonQueryProfile comparison={comparison} />
        <RunComparisonConceptGrounding comparison={comparison.conceptGroundingComparison} />
        <RunComparisonQueryAspects
          comparison={comparison.queryAspectComparison}
          formatCount={formatCount}
        />
        <RunComparisonCoverage
          comparison={comparison.coverageComparison}
          formatCount={formatCount}
        />
        <RunComparisonQualitySignals
          comparison={comparison.qualitySignalComparison}
          formatCount={formatCount}
        />
        <RunComparisonFacetCoverage
          facetComparisons={comparison.facetComparisons}
          formatCount={formatCount}
        />
        <RunComparisonRulePacks
          formatCount={formatCount}
          rulePackChanges={rulePackChanges}
        />
        <RunComparisonRankChanges
          formatCount={formatCount}
          rankChanges={comparison.rankChanges}
        />
        <RunComparisonEvidenceChange
          evidenceIds={comparison.addedEvidenceIds}
          label="Added evidence"
          variant="success"
        />
        <RunComparisonEvidenceChange
          evidenceIds={comparison.removedEvidenceIds}
          label="Removed evidence"
          variant="warning"
        />
        <RunComparisonEvidenceChange
          evidenceIds={comparison.retainedEvidenceIds}
          label="Retained evidence"
          variant="muted"
        />
      </div>
      <div className="break-words text-xs font-semibold text-muted-foreground">
        Top source: {comparison.topSourceBefore ?? "none"} to{" "}
        {comparison.topSourceAfter ?? "none"}
      </div>
    </div>
  );
}
