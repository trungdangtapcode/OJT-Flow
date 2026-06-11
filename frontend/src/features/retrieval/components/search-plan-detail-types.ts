export type QueryAspectStack = {
  aspectId: string;
  label: string;
  priority: number;
  question: string;
  rationale: string;
  ruleId: string;
  suggestedFilters: Record<string, string>;
  suggestedTerms: string[];
};

export type SearchHintStack = {
  metadata: Record<string, unknown>;
  query: string;
  rationale: string;
  target: string;
  url: string | null;
  warnings: string[];
};

export type FilterSuggestionStack = {
  applied: boolean;
  confidence: number;
  field: string;
  reason: string;
  value: string;
};
