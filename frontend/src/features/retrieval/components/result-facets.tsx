import { ListFilter, Loader2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { cn, humanize } from "../../../lib/utils";
import type { RetrievalFacetBucket, RetrievalFacets } from "../../../types";

export type ResultFacetFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level";

export type ResultFacetFilters = Partial<Record<ResultFacetFilterField | "source_id", string>>;

type FacetSection = {
  field: ResultFacetFilterField;
  label: string;
  values: RetrievalFacetBucket[];
  formatter: (value: string) => string;
};

export function ResultFacets({
  activeFilters,
  facets,
  isSearchPending,
  onApplyFacet,
}: {
  activeFilters: ResultFacetFilters;
  facets: RetrievalFacets | null | undefined;
  isSearchPending: boolean;
  onApplyFacet: (field: ResultFacetFilterField, value: string) => void;
}) {
  if (!facets) return null;
  const facetSections: FacetSection[] = [
    { field: "source_type", label: "Source type", values: facets.source_type, formatter: humanize },
    { field: "clinical_domain", label: "Domain", values: facets.clinical_domain, formatter: humanize },
    { field: "standard_system", label: "Standard", values: facets.standard_system, formatter: (value: string) => value },
    { field: "trust_level", label: "Trust", values: facets.trust_level, formatter: humanize },
  ];
  const sections = facetSections.filter((section) => section.values.length > 0);
  if (!sections.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Result facets
        </div>
        <Badge variant="muted">click to refine</Badge>
      </div>
      <div className="grid gap-2 lg:grid-cols-2">
        {sections.map((section) => (
          <div className="grid gap-1.5" key={section.label}>
            <div className="text-xs font-bold text-muted-foreground">{section.label}</div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {section.values.map((bucket) => {
                const applied = activeFilters[section.field] === bucket.value;
                return (
                  <button
                    aria-label={`Filter by ${section.label} ${section.formatter(bucket.value)}`}
                    aria-pressed={applied}
                    className={cn(
                      "inline-flex max-w-full items-center gap-1.5 rounded-full border px-2 py-1 text-xs font-bold transition-colors focus-ring disabled:cursor-not-allowed disabled:opacity-70",
                      applied
                        ? "border-emerald-200 bg-emerald-100 text-emerald-900"
                        : "border-border bg-card text-muted-foreground hover:border-primary/40 hover:bg-primary/10 hover:text-foreground",
                    )}
                    disabled={applied || isSearchPending}
                    key={`${section.label}-${bucket.value}`}
                    onClick={() => onApplyFacet(section.field, bucket.value)}
                    title={
                      applied
                        ? `${section.formatter(bucket.value)} is already applied`
                        : `Apply ${section.label}=${section.formatter(bucket.value)}`
                    }
                    type="button"
                  >
                    {isSearchPending && !applied ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <ListFilter className="h-3 w-3" />
                    )}
                    <span className="break-words">{section.formatter(bucket.value)}</span>
                    <span className="tabular-nums text-foreground">{bucket.count}</span>
                    {applied ? <span>applied</span> : null}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
