import {
  CoverageDiagnosticsPanel,
} from "./coverage-diagnostics-panel";
import { QualitySignalList } from "./quality-signal-list";
import { QueryAnalysisBlock } from "./query-analysis-block";
import { QueryVariantList } from "./query-variant-list";
import { RecommendedActionsPanel } from "./recommended-actions-panel";
import type { RetrievalTracePanelProps } from "./retrieval-trace-panel-types";
import { TokenList } from "./token-list";
import { TraceFact } from "./trace-fact";

export function RetrievalTraceContent({
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
}: RetrievalTracePanelProps & { view: NonNullable<RetrievalTracePanelProps["view"]> }) {
  return (
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
  );
}
