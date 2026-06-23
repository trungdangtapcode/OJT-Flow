import { Badge } from "../../../components/ui/badge";
import type { RetrievalFacets } from "../../../types";
import { ResultFacetBucketButton } from "./result-facet-bucket-button";
import { resultFacetSections } from "./result-facet-sections";
export type { ResultFacetFilterField, ResultFacetFilters } from "./result-facet-types";
import type { ResultFacetFilterField, ResultFacetFilters } from "./result-facet-types";

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
  const sections = resultFacetSections(facets);
  if (!sections.length) return null;
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3">
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
                  <ResultFacetBucketButton
                    applied={applied}
                    bucket={bucket}
                    field={section.field}
                    formatter={section.formatter}
                    isSearchPending={isSearchPending}
                    key={`${section.label}-${bucket.value}`}
                    label={section.label}
                    onApplyFacet={onApplyFacet}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
