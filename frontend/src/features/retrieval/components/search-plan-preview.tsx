import { BrainCircuit, CheckCircle2, Clipboard } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { Notice } from "../../../components/ui/notice";
import { humanize } from "../../../lib/utils";
import type {
  RetrievalPlanRiskSignal,
  RetrievalPlanTaskSummary,
  RetrievalQualitySummary,
  RetrievalQueryVariant,
  RetrievalSearchTask,
} from "../../../types";
import {
  SearchPlanAspectPreview,
  SearchPlanFilterSuggestionPreview,
  SearchPlanHintPreview,
  SearchPlanRewritePreview,
  type FilterSuggestionStack,
  type QueryAspectStack,
  type SearchHintStack,
} from "./search-plan-detail-panels";
import {
  SearchPlanCoverageSummaryPanel,
  SearchPlanRiskSignalsPanel,
  SearchPlanTaskSummaryPanel,
  type SearchPlanCoverageSummaryView,
} from "./search-plan-summary-panels";
import { SearchPlanTaskPreview } from "./search-plan-task-preview";
import { SectionHelpText } from "./section-help-text";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";
type SupportedPlanFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type SearchPlanPreviewProfile = {
  complexity: string;
  description: string;
  label: string;
  retrievalMode: string;
  route: string;
};

export type SearchPlanPreviewAnalysis = {
  filterSuggestions: FilterSuggestionStack[];
  queryAspects: QueryAspectStack[];
  searchHints: SearchHintStack[];
  standards: string[];
  strategy: string;
  retrievalTasks: RetrievalSearchTask[];
};

export type SearchPlanPreviewView = {
  analysis: SearchPlanPreviewAnalysis;
  coverageSummary: SearchPlanCoverageSummaryView;
  planSummary: string | null;
  profile: SearchPlanPreviewProfile | null;
  qualitySummary: RetrievalQualitySummary | null;
  riskSignals: RetrievalPlanRiskSignal[];
  taskSummary: RetrievalPlanTaskSummary;
  variants: RetrievalQueryVariant[];
};

type CopyFeedbackHook = () => {
  copiedKey: string | null;
  markCopied: (key: string) => void;
};

export function SearchPlanPreview({
  copyTextToClipboard,
  formatCount,
  formatFilterValue,
  isPlanLoading,
  isSearchPending,
  isSupportedFilterField,
  onApplyFilterSuggestion,
  onCopyPlan,
  onRunTask,
  planError,
  qualitySummaryBadgeVariant,
  useCopyFeedback,
  view,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  formatCount: (count: number, singular: string) => string;
  formatFilterValue: (field: SupportedPlanFilterField, value: string) => string;
  isPlanLoading: boolean;
  isSearchPending: boolean;
  isSupportedFilterField: (field: string) => field is SupportedPlanFilterField;
  onApplyFilterSuggestion: (suggestion: FilterSuggestionStack) => void;
  onCopyPlan: () => Promise<void>;
  onRunTask: (task: RetrievalSearchTask) => void;
  planError: string | null;
  qualitySummaryBadgeVariant: (summary: RetrievalQualitySummary) => BadgeVariant;
  useCopyFeedback: CopyFeedbackHook;
  view: SearchPlanPreviewView | null;
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const copyKey = "retrieval-search-plan-preview";

  if (!view) {
    return (
      <Card className="min-w-0 overflow-hidden">
        <CardHeader className="border-b border-border bg-card/70">
          <CardTitle className="flex items-center gap-2">
            <BrainCircuit className="h-5 w-5 text-primary" />
            Search plan
            <HelpTooltip label="Search plan help">
              After a search, this shows the backend route, generated query aspects, external medical search hints, and filter suggestions before you inspect ranked evidence.
            </HelpTooltip>
          </CardTitle>
          <CardDescription>Run a search to see how retrieval will be routed.</CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          {planError ? (
            <Notice title="Search plan unavailable" tone="danger">
              {planError}
            </Notice>
          ) : null}
          <Notice title="No search plan yet">
            Enter a query to preview the route, standards, and medical search follow-ups before running full evidence search.
          </Notice>
        </CardContent>
      </Card>
    );
  }

  const { analysis, coverageSummary, planSummary, profile, qualitySummary, riskSignals, taskSummary, variants } = view;
  const copied = copiedKey === copyKey;
  const copyPlan = async () => {
    await onCopyPlan();
    markCopied(copyKey);
  };

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2">
              <BrainCircuit className="h-5 w-5 text-primary" />
              Search plan
              <HelpTooltip label="Search plan help">
                Backend-generated plan for this evidence search. It explains the route, query rewrites, medical standards, external search hints, and suggested filters.
              </HelpTooltip>
            </CardTitle>
            <CardDescription>
              Route, aspects, rewrites, and medical follow-up searches.
            </CardDescription>
          </div>
          <Button
            aria-label="Copy search plan JSON"
            onClick={() => void copyPlan()}
            size="sm"
            type="button"
            variant="outline"
          >
            {copied ? <CheckCircle2 className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />}
            {copied ? "Copied" : "Copy plan"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-3 pt-4">
        <div className="grid min-w-0 gap-2 rounded-md border border-border bg-muted/20 p-3">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-black uppercase text-muted-foreground">
              Route decision
            </span>
            {qualitySummary ? (
              <Badge variant={qualitySummaryBadgeVariant(qualitySummary)}>
                {humanize(qualitySummary.status)} {qualitySummary.score}/100
              </Badge>
            ) : (
              <Badge variant="muted">plan only</Badge>
            )}
          </div>
          <div className="break-words text-base font-black">
            {profile?.label ?? humanize(analysis.strategy)}
          </div>
          <div className="break-words text-sm leading-6 text-muted-foreground">
            {planSummary ??
              profile?.description ??
              "The backend used the default retrieval route because no stronger query profile matched."}
          </div>
          <div className="flex min-w-0 flex-wrap gap-1.5">
            <Badge variant="muted">{humanize(analysis.strategy)}</Badge>
            {profile ? (
              <>
                <Badge variant="muted">{humanize(profile.route)}</Badge>
                <Badge variant="muted">{humanize(profile.retrievalMode)}</Badge>
                <Badge variant={profile.complexity === "high" ? "warning" : "success"}>
                  {humanize(profile.complexity)}
                </Badge>
              </>
            ) : null}
            <Badge variant={analysis.standards.length ? "success" : "muted"}>
              {formatCount(analysis.standards.length, "standard")}
            </Badge>
            <Badge variant={analysis.queryAspects.length ? "success" : "muted"}>
              {formatCount(analysis.queryAspects.length, "aspect")}
            </Badge>
          </div>
        </div>

        {isPlanLoading && !qualitySummary ? (
          <Notice title="Planning search">
            Updating route, aspects, and medical search hints from the current query.
          </Notice>
        ) : null}
        {planError ? (
          <Notice title="Search plan unavailable" tone="danger">
            {planError}
          </Notice>
        ) : null}

        <SearchPlanCoverageSummaryPanel summary={coverageSummary} />
        <SearchPlanTaskSummaryPanel
          copyTextToClipboard={copyTextToClipboard}
          isSearchPending={isSearchPending}
          onRunTask={onRunTask}
          summary={taskSummary}
          tasks={analysis.retrievalTasks}
          useCopyFeedback={useCopyFeedback}
        />
        <SearchPlanRiskSignalsPanel signals={riskSignals} />
        <SearchPlanTaskPreview
          copyTextToClipboard={copyTextToClipboard}
          isSearchPending={isSearchPending}
          onRunTask={onRunTask}
          tasks={analysis.retrievalTasks}
          useCopyFeedback={useCopyFeedback}
        />
        <SearchPlanAspectPreview aspects={analysis.queryAspects} />
        <SearchPlanRewritePreview variants={variants} />
        <SearchPlanHintPreview hints={analysis.searchHints} />

        <div className="grid min-w-0 gap-2 rounded-md border border-border bg-muted/20 p-3">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-black uppercase text-muted-foreground">
              Suggested filters
            </span>
            <Badge variant={analysis.filterSuggestions.length ? "warning" : "success"}>
              {analysis.filterSuggestions.length
                ? formatCount(analysis.filterSuggestions.length, "suggestion")
                : "none"}
            </Badge>
          </div>
          {analysis.filterSuggestions.length ? (
            <div className="grid gap-1.5">
              {analysis.filterSuggestions.slice(0, 4).map((suggestion) => (
                <SearchPlanFilterSuggestionPreview
                  displayValue={
                    isSupportedFilterField(suggestion.field)
                      ? formatFilterValue(suggestion.field, suggestion.value)
                      : suggestion.value
                  }
                  isSearchPending={isSearchPending}
                  key={`${suggestion.field}-${suggestion.value}-${suggestion.reason}`}
                  onApplySuggestion={onApplyFilterSuggestion}
                  suggestion={suggestion}
                  supported={isSupportedFilterField(suggestion.field)}
                />
              ))}
            </div>
          ) : (
            <SectionHelpText>
              No additional metadata filters were suggested for this query.
            </SectionHelpText>
          )}
        </div>

        {isSearchPending ? (
          <Notice title="Search running">
            The current results may be updating. Wait for completion before using this plan for review notes.
          </Notice>
        ) : null}
      </CardContent>
    </Card>
  );
}
