import { ListFilter } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { Notice } from "../../../components/ui/notice";
import type {
  RetrievalCoverage,
  RetrievalCoverageItem,
  RetrievalQualitySignal,
  RetrievalQueryVariant,
  RetrievalRecommendedAction,
} from "../../../types";
import {
  CoverageDiagnosticsPanel,
  type CoverageDiagnosticsFilterAction,
  type CoverageDiagnosticsFilterField,
} from "./coverage-diagnostics-panel";
import { QualitySignalList } from "./quality-signal-list";
import { QueryAnalysisBlock, type QueryAnalysisBlockView } from "./query-analysis-block";
import { QueryVariantList } from "./query-variant-list";
import {
  RecommendedActionsPanel,
  type RecommendedActionFilter,
  type RecommendedActionFilterField,
} from "./recommended-actions-panel";
import type { FilterSuggestionStack } from "./search-plan-detail-panels";
import { TokenList } from "./token-list";
import { TraceFact } from "./trace-fact";

export type RetrievalTracePanelView = {
  coverage: RetrievalCoverage | null | undefined;
  facts: { label: string; value: string }[];
  filtersApplied: Record<string, unknown>;
  qualitySignals: RetrievalQualitySignal[];
  queryAnalysis: QueryAnalysisBlockView | null;
  queryVariants: RetrievalQueryVariant[];
  recommendedActions: RetrievalRecommendedAction[];
  safetyFlags: string[];
  warnings: string[];
};

type TracePanelActiveFilter = {
  field: RecommendedActionFilterField;
};

export function RetrievalTracePanel({
  activeFilters,
  filterFieldLabel,
  formatCount,
  formatFilterValue,
  getActionFilter,
  getActionSourceLabel,
  getCoverageSuggestedAction,
  getCoverageSuggestedFilter,
  isSearchPending,
  isSuggestionSupported,
  onApplyCoverageFilter,
  onApplyFilterSuggestion,
  onClearAllFilters,
  onClearSourceScope,
  view,
}: {
  activeFilters: TracePanelActiveFilter[];
  filterFieldLabel: (field: RecommendedActionFilterField) => string;
  formatCount: (count: number, singular: string) => string;
  formatFilterValue: (field: RecommendedActionFilterField, value: string) => string;
  getActionFilter: (action: RetrievalRecommendedAction) => RecommendedActionFilter | null;
  getActionSourceLabel: (action: RetrievalRecommendedAction) => string | null;
  getCoverageSuggestedAction: (item: RetrievalCoverageItem) => string;
  getCoverageSuggestedFilter: (
    item: RetrievalCoverageItem,
  ) => CoverageDiagnosticsFilterAction | null;
  isSearchPending: boolean;
  isSuggestionSupported: (field: string) => boolean;
  onApplyCoverageFilter: (field: CoverageDiagnosticsFilterField, value: string) => void;
  onApplyFilterSuggestion: (suggestion: FilterSuggestionStack) => void;
  onClearAllFilters: () => void;
  onClearSourceScope: () => void;
  view: RetrievalTracePanelView | null;
}) {
  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="border-b border-border bg-card/70">
        <CardTitle className="flex items-center gap-2">
          <ListFilter className="h-5 w-5 text-primary" />
          Retrieval trace
          <HelpTooltip label="Retrieval trace help">
            Trace shows how the backend transformed the query, which filters were applied, and which quality or safety issues affected the evidence package.
          </HelpTooltip>
        </CardTitle>
        <CardDescription>Query route, rewrites, filters, warnings, and quality diagnostics.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 pt-4">
        {!view ? (
          <Notice title="Trace unavailable">Run a search to inspect the trace.</Notice>
        ) : (
          <>
            {view.facts.map((fact) => (
              <TraceFact key={fact.label} label={fact.label} value={fact.value} />
            ))}
            <TraceFact
              label="Filters"
              value={
                Object.keys(view.filtersApplied).length
                  ? JSON.stringify(view.filtersApplied)
                  : "none"
              }
            />
            <QualitySignalList signals={view.qualitySignals} />
            <RecommendedActionsPanel
              activeFilters={activeFilters}
              actions={view.recommendedActions}
              filterFieldLabel={filterFieldLabel}
              formatFilterValue={formatFilterValue}
              getActionFilter={getActionFilter}
              getActionSourceLabel={getActionSourceLabel}
              isSearchPending={isSearchPending}
              onApplyFilter={onApplyCoverageFilter}
              onClearAllFilters={onClearAllFilters}
              onClearSourceScope={onClearSourceScope}
            />
            <QueryAnalysisBlock
              analysis={view.queryAnalysis}
              formatCount={formatCount}
              isSearchPending={isSearchPending}
              isSuggestionSupported={isSuggestionSupported}
              onApplyFilterSuggestion={onApplyFilterSuggestion}
            />
            <CoverageDiagnosticsPanel
              coverage={view.coverage}
              filterFieldLabel={filterFieldLabel}
              formatFilterValue={formatFilterValue}
              getCoverageSuggestedAction={getCoverageSuggestedAction}
              getCoverageSuggestedFilter={getCoverageSuggestedFilter}
              isSearchPending={isSearchPending}
              onApplyCoverageFilter={onApplyCoverageFilter}
            />
            <QueryVariantList variants={view.queryVariants} />
            <TokenList
              description="Safety-sensitive context detected in the retrieval request. Treat query text as untrusted data."
              items={view.safetyFlags}
              title="Safety flags"
              tone="warning"
            />
            <TokenList
              description="Backend warnings about search coverage, fallbacks, or risky context."
              items={view.warnings}
              title="Warnings"
              tone="warning"
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
