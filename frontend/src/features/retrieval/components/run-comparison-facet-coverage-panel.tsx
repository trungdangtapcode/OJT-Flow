import { Badge } from "../../../components/ui/badge";
import type { BadgeVariant, RetrievalFacetComparisonView } from "./run-comparison-detail-types";

export function RunComparisonFacetCoverage({
  facetComparisons,
  formatCount,
}: {
  facetComparisons: RetrievalFacetComparisonView[];
  formatCount: (count: number, singular: string) => string;
}) {
  if (!facetComparisons.length) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Facet coverage</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Facet coverage</span>
        <Badge variant="muted">{formatCount(facetComparisons.length, "facet")}</Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {facetComparisons.map((facet) => (
          <div
            className="grid gap-1 rounded-md bg-muted/40 px-2 py-1.5"
            key={facet.field}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="font-bold">{facet.label}</span>
              <Badge variant={facet.addedValues.length || facet.removedValues.length ? "warning" : "success"}>
                {facet.baselineCount} to {facet.activeCount}
              </Badge>
            </div>
            <FacetValueChange values={facet.addedValues} label="Added" variant="success" />
            <FacetValueChange values={facet.removedValues} label="Removed" variant="warning" />
            <FacetValueChange values={facet.retainedValues} label="Retained" variant="muted" />
          </div>
        ))}
      </div>
    </div>
  );
}

function FacetValueChange({
  label,
  values,
  variant,
}: {
  label: string;
  values: string[];
  variant: BadgeVariant;
}) {
  if (!values.length) return null;
  return (
    <div className="flex min-w-0 flex-wrap gap-1">
      <span className="font-semibold text-muted-foreground">{label}:</span>
      {values.slice(0, 4).map((value) => (
        <Badge key={`${label}-${value}`} variant={variant}>
          {value}
        </Badge>
      ))}
      {values.length > 4 ? <Badge variant="muted">+{values.length - 4}</Badge> : null}
    </div>
  );
}
