import { AlertTriangle, ListFilter, X } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";

export type NoResultFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type NoResultActiveFilter = {
  displayValue: string;
  field: NoResultFilterField;
  label: string;
};

export type NoResultSuggestedAction = {
  field: NoResultFilterField;
  value: string;
};

export function NoResultRemediationPanel({
  candidateCount,
  filterFieldLabel,
  isSearchPending,
  missingBucketCount,
  onApplyFacet,
  onClearAllFilters,
  onClearFilter,
  submittedFilters,
  suggestedAction,
}: {
  candidateCount: number;
  filterFieldLabel: (field: NoResultFilterField) => string;
  isSearchPending: boolean;
  missingBucketCount: number;
  onApplyFacet: (field: NoResultFilterField, value: string) => void;
  onClearAllFilters: () => void;
  onClearFilter: (field: NoResultFilterField) => void;
  submittedFilters: NoResultActiveFilter[];
  suggestedAction: NoResultSuggestedAction | null;
}) {
  const sourceFilter = submittedFilters.find((filter) => filter.field === "source_id");
  return (
    <div className="grid gap-3 rounded-md border border-amber-200 bg-amber-50 p-4">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-sm font-black">
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-700" />
            No matching evidence returned
          </div>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">
            The backend completed the search, but no ranked evidence hit is available for this exact request. Use the remediation checks below before trusting the result as evidence absence.
          </p>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant="warning">{formatCount(candidateCount, "candidate")}</Badge>
          {missingBucketCount ? (
            <Badge variant="warning">{formatCount(missingBucketCount, "required gap")}</Badge>
          ) : null}
          {submittedFilters.length ? (
            <Badge variant="muted">{formatCount(submittedFilters.length, "active filter")}</Badge>
          ) : null}
        </div>
      </div>
      <div className="grid gap-2 md:grid-cols-3">
        <NoResultActionCard
          text={
            submittedFilters.length
              ? "The submitted search has active filters. Remove exact source, standard, domain, or trust filters if you need broader evidence."
              : "Try fewer exact terms, add field names, or start from a trusted preset when the query is too narrow."
          }
          title={submittedFilters.length ? "Loosen scope" : "Broaden query"}
        >
          {submittedFilters.length ? (
            <div className="grid gap-2">
              <div className="flex min-w-0 flex-wrap gap-1.5">
                {submittedFilters.map((filter) => (
                  <Badge className="max-w-full break-words" key={filter.field} variant="muted">
                    {filter.label}: {filter.displayValue}
                  </Badge>
                ))}
              </div>
              <div className="flex min-w-0 flex-wrap gap-1.5">
                {sourceFilter ? (
                  <Button
                    disabled={isSearchPending}
                    onClick={() => onClearFilter("source_id")}
                    size="sm"
                    title="Clear exact source scope and rerun search"
                    type="button"
                    variant="outline"
                  >
                    <X className="h-4 w-4" />
                    Clear source scope
                  </Button>
                ) : null}
                <Button
                  disabled={isSearchPending}
                  onClick={onClearAllFilters}
                  size="sm"
                  title="Clear all active metadata filters and rerun search"
                  type="button"
                  variant="outline"
                >
                  <ListFilter className="h-4 w-4" />
                  Clear all filters
                </Button>
              </div>
            </div>
          ) : null}
        </NoResultActionCard>
        <NoResultActionCard
          text={
            candidateCount
              ? "Candidates were seen, so review readiness, evidence buckets, and strategy recommendations for why none became usable hits."
              : "No candidates were seen. Reindex the trusted corpus or confirm the source inventory contains the domain and standard you need."
          }
          title={candidateCount ? "Inspect quality gaps" : "Check source inventory"}
        />
        <NoResultActionCard
          text={
            suggestedAction
              ? "A backend corrective action has a supported filter. Apply it only if it matches the evidence class you need."
              : "No supported corrective filter was returned. Use a preset or adjust schema, format, fields, and source scope."
          }
          title={suggestedAction ? "Apply backend suggestion" : "Use guided presets"}
        >
          {suggestedAction ? (
            <Button
              disabled={isSearchPending}
              onClick={() => onApplyFacet(suggestedAction.field, suggestedAction.value)}
              size="sm"
              type="button"
              variant="outline"
            >
              <ListFilter className="h-4 w-4" />
              Apply {filterFieldLabel(suggestedAction.field)}
            </Button>
          ) : null}
        </NoResultActionCard>
      </div>
    </div>
  );
}

function NoResultActionCard({
  children,
  text,
  title,
}: {
  children?: ReactNode;
  text: string;
  title: string;
}) {
  return (
    <div className="grid content-start gap-2 rounded-md border border-amber-200 bg-card px-3 py-2">
      <div className="font-black">{title}</div>
      <p className="text-sm leading-6 text-muted-foreground">{text}</p>
      {children}
    </div>
  );
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
