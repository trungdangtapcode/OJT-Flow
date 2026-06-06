import { ExternalLink, SlidersHorizontal } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { RetrievalQueryVariant } from "../../../types";
import { SectionHelpText } from "./section-help-text";

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

export function SearchPlanAspectPreview({ aspects }: { aspects: QueryAspectStack[] }) {
  if (!aspects.length) {
    return (
      <div className="rounded-md border border-border bg-card p-3">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Search aspects
        </div>
        <SectionHelpText>
          No decomposed medical search aspects matched. Add fields, standards, or a more specific operation to improve planning.
        </SectionHelpText>
      </div>
    );
  }
  return (
    <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Search aspects
        </span>
        <Badge variant="muted">{formatCount(aspects.length, "aspect")}</Badge>
      </div>
      {aspects.slice(0, 4).map((aspect) => (
        <div className="grid gap-1 text-xs" key={aspect.aspectId}>
          <div className="flex min-w-0 flex-wrap items-center gap-1.5">
            <Badge variant="muted">P{aspect.priority}</Badge>
            <span className="break-words font-black">{aspect.label}</span>
          </div>
          <div className="break-words text-muted-foreground">{aspect.question}</div>
        </div>
      ))}
    </div>
  );
}

export function SearchPlanRewritePreview({ variants }: { variants: RetrievalQueryVariant[] }) {
  if (!variants.length) return null;
  return (
    <details className="rounded-md border border-border bg-card">
      <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-2 px-3 py-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Query rewrites
        </span>
        <Badge variant="muted">{formatCount(variants.length, "variant")}</Badge>
      </summary>
      <div className="grid gap-2 border-t border-border p-3">
        {variants.slice(0, 6).map((variant, index) => (
          <div className="grid gap-1 text-xs" key={`${variant.source}-${variant.variant}-${index}`}>
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <Badge variant="muted">{humanize(variant.source)}</Badge>
              <span className="break-words font-semibold text-muted-foreground">
                {variant.reason}
              </span>
            </div>
            <code className="max-w-full break-words rounded bg-muted px-2 py-1 font-mono">
              {variant.variant}
            </code>
          </div>
        ))}
      </div>
    </details>
  );
}

export function SearchPlanHintPreview({ hints }: { hints: SearchHintStack[] }) {
  if (!hints.length) {
    return (
      <div className="rounded-md border border-border bg-card p-3">
        <div className="text-xs font-black uppercase text-muted-foreground">
          Medical search hints
        </div>
        <SectionHelpText>
          No external medical search target matched. Queries about PubMed, trials, FHIR, LOINC, UCUM, or openFDA will show scoped syntax here.
        </SectionHelpText>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Medical search hints
        </span>
        <Badge variant="success">{formatCount(hints.length, "target")}</Badge>
      </div>
      {hints.slice(0, 3).map((hint) => (
        <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-1.5 text-xs" key={`${hint.target}-${hint.query}`}>
          <div className="flex min-w-0 flex-wrap items-center justify-start gap-1.5 sm:justify-between">
            <span className="break-words font-black">{humanize(hint.target)}</span>
            {hint.url ? (
              <Button asChild size="sm" title="Open medical search hint" variant="outline">
                <a href={hint.url} rel="noopener noreferrer" target="_blank">
                  <ExternalLink className="h-4 w-4" />
                  Open
                </a>
              </Button>
            ) : null}
          </div>
          <code className="block max-w-full overflow-hidden break-words rounded bg-muted px-2 py-1 font-mono">
            {hint.query}
          </code>
        </div>
      ))}
    </div>
  );
}

export function SearchPlanFilterSuggestionPreview({
  displayValue,
  isSearchPending,
  onApplySuggestion,
  suggestion,
  supported,
}: {
  displayValue: string;
  isSearchPending: boolean;
  onApplySuggestion: (suggestion: FilterSuggestionStack) => void;
  suggestion: FilterSuggestionStack;
  supported: boolean;
}) {
  return (
    <div className="grid gap-1 rounded-md border border-border bg-card px-2 py-1.5 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-1.5">
        <div className="flex min-w-0 flex-wrap items-center gap-1.5">
          <Badge variant={suggestion.applied ? "success" : supported ? "muted" : "warning"}>
            {suggestion.applied ? "applied" : supported ? "available" : "unsupported"}
          </Badge>
          <span className="break-words font-black">
            {humanize(suggestion.field)}={displayValue}
          </span>
        </div>
        {supported ? (
          <Button
            disabled={isSearchPending || suggestion.applied}
            onClick={() => onApplySuggestion(suggestion)}
            size="sm"
            type="button"
            variant="outline"
          >
            <SlidersHorizontal className="h-4 w-4" />
            Apply
          </Button>
        ) : null}
      </div>
      <div className="break-words text-muted-foreground">{suggestion.reason}</div>
    </div>
  );
}

function formatCount(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}
