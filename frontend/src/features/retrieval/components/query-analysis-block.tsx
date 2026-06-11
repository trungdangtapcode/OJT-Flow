import { ConceptCandidateList } from "./concept-candidate-list";
import { FilterSuggestionList } from "./filter-suggestion-list";
import { QueryAspectPlan } from "./query-aspect-plan";
import { QueryAnalysisHeader } from "./query-analysis-header";
import { QueryDiagnosticList } from "./query-diagnostic-list";
import { QueryProfileCard } from "./query-profile-card";
import type { FilterSuggestionStack } from "./search-plan-detail-panels";
import { SearchHintList } from "./search-hint-list";
import { QueryAnalysisTokenSections } from "./query-analysis-token-sections";
import { TraceFact } from "./trace-fact";
import type { QueryAnalysisBlockView } from "./query-analysis-block-types";

export function QueryAnalysisBlock({
  analysis,
  formatCount,
  isSearchPending,
  isSuggestionSupported,
  onApplyFilterSuggestion,
}: {
  analysis: QueryAnalysisBlockView | null;
  formatCount: (count: number, singular: string) => string;
  isSearchPending: boolean;
  isSuggestionSupported: (field: string) => boolean;
  onApplyFilterSuggestion: (suggestion: FilterSuggestionStack) => void;
}) {
  if (!analysis) {
    return <TraceFact label="Query analysis" value="unavailable" />;
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <QueryAnalysisHeader
        conceptCount={analysis.detectedConcepts.length}
        ruleCount={analysis.ruleIds.length}
        standardCount={analysis.standards.length}
        strategy={analysis.strategy}
        variantCount={analysis.variantCount}
      />
      <QueryProfileCard
        filterEntries={analysis.queryProfileFilterEntries}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilterSuggestion}
        profile={analysis.queryProfile}
        routeHelpText={analysis.queryProfileRouteHelpText}
      />
      <QueryAspectPlan
        aspects={analysis.queryAspects}
        formatCount={formatCount}
        isSearchPending={isSearchPending}
        onApplyFilter={onApplyFilterSuggestion}
      />
      <QueryDiagnosticList diagnostics={analysis.diagnostics} />
      <ConceptCandidateList candidates={analysis.conceptCandidates} />
      <SearchHintList hints={analysis.searchHints} />
      <QueryAnalysisTokenSections
        detectedConcepts={analysis.detectedConcepts}
        expandedTerms={analysis.expandedTerms}
        standards={analysis.standards}
      />
      <FilterSuggestionList
        isSearchPending={isSearchPending}
        isSuggestionSupported={isSuggestionSupported}
        onApplySuggestion={onApplyFilterSuggestion}
        suggestions={analysis.filterSuggestions}
      />
    </div>
  );
}
