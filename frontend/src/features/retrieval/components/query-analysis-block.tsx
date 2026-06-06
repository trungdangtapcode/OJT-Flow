import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import { ConceptCandidateList, type ConceptCandidateListItem } from "./concept-candidate-list";
import { FilterSuggestionList } from "./filter-suggestion-list";
import {
  QueryAspectPlan,
  type QueryAspectPlanItemView,
} from "./query-aspect-plan";
import {
  QueryDiagnosticList,
  type QueryDiagnosticListItem,
} from "./query-diagnostic-list";
import {
  QueryProfileCard,
  type QueryProfileCardView,
  type QueryProfileFilterEntryView,
} from "./query-profile-card";
import type {
  FilterSuggestionStack,
  SearchHintStack,
} from "./search-plan-detail-panels";
import { SearchHintList } from "./search-hint-list";
import { TokenList } from "./token-list";
import { TraceFact } from "./trace-fact";

export type QueryAnalysisBlockView = {
  conceptCandidates: ConceptCandidateListItem[];
  detectedConcepts: string[];
  diagnostics: QueryDiagnosticListItem[];
  expandedTerms: string[];
  filterSuggestions: FilterSuggestionStack[];
  queryAspects: QueryAspectPlanItemView[];
  queryProfile: QueryProfileCardView | null;
  queryProfileFilterEntries: QueryProfileFilterEntryView[];
  queryProfileRouteHelpText: string;
  ruleIds: string[];
  searchHints: SearchHintStack[];
  standards: string[];
  strategy: string;
  variantCount: number;
};

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
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Query analysis
        </div>
        <Badge variant="muted">{analysis.strategy}</Badge>
      </div>
      <div className="grid gap-2 text-xs sm:grid-cols-4">
        <QueryAnalysisCounter label="Concepts" value={analysis.detectedConcepts.length} />
        <QueryAnalysisCounter label="Standards" value={analysis.standards.length} />
        <QueryAnalysisCounter label="Rules" value={analysis.ruleIds.length} />
        <QueryAnalysisCounter label="Variants" value={analysis.variantCount} />
      </div>
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
      <TokenList items={analysis.detectedConcepts.map(humanize)} title="Detected concepts" />
      <TokenList items={analysis.standards} title="Standard cues" />
      <FilterSuggestionList
        isSearchPending={isSearchPending}
        isSuggestionSupported={isSuggestionSupported}
        onApplySuggestion={onApplyFilterSuggestion}
        suggestions={analysis.filterSuggestions}
      />
      <TokenList items={analysis.expandedTerms} title="Expanded terms" />
    </div>
  );
}

function QueryAnalysisCounter({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border bg-card px-2 py-1.5">
      <div className="font-bold text-muted-foreground">{label}</div>
      <div className="text-base font-black tabular-nums">{value}</div>
    </div>
  );
}
