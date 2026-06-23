import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalSearchPayload } from "../../../types";
import {
  searchRunQualityBadgeVariant,
  searchRunRemediationSummary,
  searchRunScopeLabels,
  type SearchRunSummaryView,
} from "../model/search-run-presentation";
import {
  coverageGapSummaryBadgeView,
  groundedConceptSummaryBadgeView,
  searchAspectSummaryBadgeView,
} from "./search-run-evidence-summary-view";

type SearchRunEvidenceSummaryRun = {
  payload: RetrievalSearchPayload;
  summary: SearchRunSummaryView & {
    conceptGrounding: unknown[];
    coverage: unknown[];
    queryAspects: unknown[];
  };
};

export function SearchRunEvidenceSummary({ run }: { run: SearchRunEvidenceSummaryRun }) {
  const scopeLabels = searchRunScopeLabels(run.payload);
  const qualitySummary = run.summary.qualitySummary;
  const remediationSummary =
    run.summary.remediationSummary ?? searchRunRemediationSummary(run.summary);
  const coverageGapBadge = coverageGapSummaryBadgeView(run.summary.coverage.length);
  const groundedConceptBadge = groundedConceptSummaryBadgeView(
    run.summary.conceptGrounding.length,
  );
  const searchAspectBadge = searchAspectSummaryBadgeView(run.summary.queryAspects.length);

  return (
    <span className="grid min-w-0 gap-1 rounded-lg border border-border/60/70 bg-background/55 p-2">
      <span className="text-xs font-bold uppercase text-muted-foreground">
        Run scope
      </span>
      <span className="flex min-w-0 flex-wrap gap-1.5">
        {qualitySummary ? (
          <Badge variant={searchRunQualityBadgeVariant(qualitySummary)}>
            quality {humanize(qualitySummary.status)} {qualitySummary.score}
          </Badge>
        ) : null}
        <Badge variant={coverageGapBadge.variant}>{coverageGapBadge.label}</Badge>
        <Badge variant={groundedConceptBadge.variant}>{groundedConceptBadge.label}</Badge>
        <Badge variant={searchAspectBadge.variant}>{searchAspectBadge.label}</Badge>
        {scopeLabels.map((label) => (
          <Badge key={label} variant="muted">
            {label}
          </Badge>
        ))}
      </span>
      {qualitySummary?.top_action ? (
        <span className="min-w-0 break-words text-xs font-semibold text-muted-foreground">
          Top action: {qualitySummary.top_action}
        </span>
      ) : null}
      {remediationSummary ? (
        <span className="min-w-0 break-words rounded-sm bg-muted px-2 py-1 text-xs font-semibold text-muted-foreground">
          Run remediation: {remediationSummary}
        </span>
      ) : null}
    </span>
  );
}
