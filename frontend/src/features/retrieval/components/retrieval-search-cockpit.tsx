import { useEffect, useState } from "react";
import { CheckCircle2, Clipboard, ListFilter, X } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { humanize } from "../../../lib/utils";
import type {
  RetrievalSearchCockpitActiveFilter,
  RetrievalSearchCockpitView,
} from "../model/retrieval-cockpit-view-model";
import {
  CockpitMetricCard,
  QueryHealthPanel,
  SearchReadinessChecklist,
} from "./search-cockpit-panels";
import { SourceDiversityPanel } from "./source-diversity-panel";
import {
  StandardSearchPlanPanel,
  StrategyRecommendationsPanel,
  type SearchPlanFilterAction,
  type SearchPlanFilterField,
} from "./strategy-standard-panels";

export function RetrievalSearchCockpit({
  copyTextToClipboard,
  filterFieldLabel,
  getSuggestedFilterAction,
  isSearchPending,
  onApplyFilter,
  onClearAllFilters,
  onClearSourceScope,
  reportJson,
  view,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  filterFieldLabel: (field: SearchPlanFilterField) => string;
  getSuggestedFilterAction: (value: unknown) => SearchPlanFilterAction | null;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearSourceScope: () => void;
  reportJson: string;
  view: RetrievalSearchCockpitView;
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
    <section
      aria-label="Retrieval cockpit"
      className="grid gap-3 rounded-md border border-border bg-muted/20 p-3"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Search cockpit
          </div>
          <div className="mt-1 break-words text-lg font-black leading-tight">
            {view.routeLabel}
          </div>
          <div className="mt-1 flex min-w-0 flex-wrap gap-1.5">
            <Badge variant="muted">{humanize(view.strategy)}</Badge>
            <Badge variant="muted">{formatCount(view.candidateCount, "candidate")}</Badge>
            <Badge variant="muted">{formatCount(view.hitCount, "hit")}</Badge>
            {view.bm25Enabled !== null ? (
              <Badge variant={view.bm25Enabled ? "success" : "muted"}>
                BM25 {view.bm25Enabled ? "on" : "off"}
              </Badge>
            ) : null}
            <Badge variant={view.rerankerEnabled ? "success" : "muted"}>
              rerank {view.rerankerEnabled ? "on" : "off"}
            </Badge>
            {view.activeFilters.map((filter) => (
              <Badge key={filter.field} variant="muted">
                {filter.label}: {filter.displayValue}
              </Badge>
            ))}
          </div>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Button
            aria-label="Copy retrieval cockpit report"
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
            {reportCopied ? "Copied" : "Copy cockpit JSON"}
          </Button>
          <HelpTooltip label="Cockpit JSON report help">
            Copies the current retrieval package summary: submitted payload, route, ranking stack, readiness, evidence buckets, compact hits, actions, and rule-pack fingerprints.
          </HelpTooltip>
          {view.qualitySummary ? (
            <Badge variant={view.qualitySummary.variant}>
              {humanize(view.qualitySummary.status)} {view.qualitySummary.score}/100
            </Badge>
          ) : null}
          <Badge
            variant={
              view.requiredBucketCount &&
              view.coveredRequiredBucketCount < view.requiredBucketCount
                ? "warning"
                : "success"
            }
          >
            {view.requiredBucketCount
              ? `${view.coveredRequiredBucketCount}/${view.requiredBucketCount} required buckets`
              : "no required buckets"}
          </Badge>
          <Badge variant={view.coverageGapCount ? "warning" : "success"}>
            {view.coverageGapCount
              ? formatCount(view.coverageGapCount, "coverage gap")
              : "coverage ok"}
          </Badge>
        </div>
      </div>

      <QueryHealthPanel
        activeFilters={view.activeFilters}
        isSearchPending={isSearchPending}
        items={view.queryHealth}
        onClearAllFilters={onClearAllFilters}
        onClearSourceScope={onClearSourceScope}
      />

      <SearchReadinessChecklist items={view.readinessChecklist} />

      <div className="grid gap-2 lg:grid-cols-5">
        <CockpitMetricCard
          helpText="The backend route chosen for this query, such as broad, structured, or safety-sensitive search. Use this to confirm the search behavior matches the question."
          label="Retrieval route"
          supporting={view.queryProfile ? humanize(view.queryProfile.route) : view.strategy}
          tone="info"
          value={view.queryProfile ? humanize(view.queryProfile.complexity) : "standard"}
        />
        <CockpitMetricCard
          helpText="The retrieval stack combines lexical search, vector search, and optional reranking. Stronger stacks usually improve recall and ordering, but still need evidence review."
          label="Hybrid stack"
          supporting={view.rankingSupporting}
          tone="success"
          value={view.hybridStackValue}
        />
        <CockpitMetricCard
          helpText="Whether lexical and vector retrieval agree on the same top candidates. Low agreement means inspect query wording, filters, and reranking before trusting order."
          label="Fusion agreement"
          supporting={view.fusionDiagnostics.interpretation}
          tone={view.fusionDiagnostics.tone}
          value={view.fusionDiagnostics.label}
        />
        <CockpitMetricCard
          helpText="How many independent sources survived source-diversity selection. Low spread can mean the answer depends on one source family."
          label="Evidence spread"
          supporting={
            view.diversity.enabled
              ? `${formatCount(view.diversity.selectedSourceCount, "selected source")}`
              : "source diversity disabled"
          }
          tone={view.diversity.enabled ? "success" : "warning"}
          value={formatSourceCoverage(view.diversity)}
        />
        <CockpitMetricCard
          helpText="Concepts and query aspects detected from the search. Good grounding means the result matched the intended medical data concept, not just similar words."
          label="Grounding"
          supporting={formatCount(view.queryAspectCount, "query aspect")}
          tone={view.conceptGroundingCount ? "success" : "warning"}
          value={formatCount(view.conceptGroundingCount, "concept")}
        />
      </div>

      <StrategyRecommendationsPanel
        getSuggestedFilterAction={getSuggestedFilterAction}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilter}
        recommendations={view.strategyRecommendations}
      />

      <StandardSearchPlanPanel
        getSuggestedFilterAction={getSuggestedFilterAction}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilter}
        plan={view.standardSearchPlan}
      />

      <SourceDiversityPanel diversity={view.diversity} isSearchPending={isSearchPending} />

      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(320px,0.75fr)]">
        <div className="grid gap-2 rounded-md border border-border bg-card p-3">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <div className="text-xs font-black uppercase text-muted-foreground">
              Query transformation
            </div>
            <Badge variant="muted">{formatCount(view.variantCount, "variant")}</Badge>
          </div>
          <div className="flex min-w-0 flex-wrap gap-1.5">
            {view.standards.slice(0, 8).map((standard) => (
              <Badge key={standard} variant="success">
                {standard}
              </Badge>
            ))}
            {view.detectedConcepts.slice(0, 8).map((concept) => (
              <Badge key={concept} variant="muted">
                {humanize(concept)}
              </Badge>
            ))}
            {view.expandedTerms.slice(0, 10).map((term) => (
              <span
                className="max-w-full break-words rounded-full border border-border bg-muted px-2.5 py-1 text-xs font-bold text-muted-foreground"
                key={term}
              >
                {term}
              </span>
            ))}
          </div>
          {view.queryAspects.length ? (
            <div className="grid gap-1.5">
              {view.queryAspects.slice(0, 3).map((aspect) => (
                <div
                  className="grid gap-1 rounded-md border border-border bg-muted/25 px-3 py-2 text-xs"
                  key={aspect.aspectId}
                >
                  <div className="flex min-w-0 flex-wrap items-center gap-1.5">
                    <Badge variant="muted">P{aspect.priority}</Badge>
                    <span className="break-words font-black">{aspect.label}</span>
                  </div>
                  <div className="break-words text-muted-foreground">
                    {aspect.question}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div className="grid gap-2 rounded-md border border-border bg-card p-3">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <div className="text-xs font-black uppercase text-muted-foreground">
              Next best action
            </div>
            {view.correctiveActionCount !== null ? (
              <Badge variant={view.correctiveActionCount ? "warning" : "success"}>
                {formatCount(view.correctiveActionCount, "action")}
              </Badge>
            ) : null}
          </div>
          <div className="break-words text-sm font-black">
            {view.topAction?.title ??
              view.qualitySummary?.topAction ??
              "No corrective action required"}
          </div>
          <div className="break-words text-sm leading-6 text-muted-foreground">
            {view.topAction?.description ??
              "Review the ranked evidence, source provenance, and judgment metrics before using the package downstream."}
          </div>
          {view.topFilterAction ? (
            <Button
              disabled={isSearchPending}
              onClick={() =>
                onApplyFilter(view.topFilterAction!.field, view.topFilterAction!.value)
              }
              size="sm"
              type="button"
              variant="outline"
            >
              <ListFilter className="h-4 w-4" />
              Apply {filterFieldLabel(view.topFilterAction.field)}
            </Button>
          ) : null}
          {view.topBroadeningAction ? (
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {view.activeFilters.some((filter) => filter.field === "source_id") ? (
                <Button
                  disabled={isSearchPending}
                  onClick={onClearSourceScope}
                  size="sm"
                  title="Clear exact source scope and rerun search"
                  type="button"
                  variant="outline"
                >
                  <X className="h-4 w-4" />
                  Clear source scope
                </Button>
              ) : null}
              <Button
                disabled={isSearchPending || !view.activeFilters.length}
                onClick={onClearAllFilters}
                size="sm"
                title="Clear all active metadata filters and rerun search"
                type="button"
                variant="outline"
              >
                <ListFilter className="h-4 w-4" />
                Broaden search
              </Button>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function formatCount(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function formatSourceCoverage(diversity: RetrievalSearchCockpitView["diversity"]): string {
  if (!diversity.enabled) return "off";
  return `${diversity.selectedSourceCount}/${diversity.candidateSourceCount}`;
}
