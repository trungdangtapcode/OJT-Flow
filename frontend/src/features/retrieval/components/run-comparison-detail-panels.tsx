import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";

type BadgeVariant = "success" | "warning" | "muted";

export type QueryProfileSummaryView = {
  complexity: string;
  label: string;
  profileId: string;
  retrievalMode: string;
  route: string;
};

export type RunComparisonQueryProfileView = {
  activeSummary: { queryProfile: QueryProfileSummaryView | null };
  baselineSummary: { queryProfile: QueryProfileSummaryView | null };
  queryProfileChanged: boolean;
};

export type ConceptGroundingSummaryView = {
  code: string | null;
  conceptId: string;
  displayName: string;
  evidenceCount: number;
  standardSystem: string;
};

export type RetrievalConceptGroundingComparisonView = {
  added: ConceptGroundingSummaryView[];
  removed: ConceptGroundingSummaryView[];
  retained: ConceptGroundingSummaryView[];
};

export type QueryAspectSummaryView = {
  aspectId: string;
  label: string;
  priority: number;
  question: string;
  ruleId: string;
};

export type RetrievalQueryAspectComparisonView = {
  added: QueryAspectSummaryView[];
  removed: QueryAspectSummaryView[];
  retained: QueryAspectSummaryView[];
};

export type RetrievalCoverageSummaryView = {
  field: string;
  label: string;
  selectedCount: number;
  status: string;
  suggestedFilter: Record<string, string>;
  value: string;
};

export type RetrievalCoverageStatusChangeView = {
  active: RetrievalCoverageSummaryView;
  baseline: RetrievalCoverageSummaryView;
};

export type RetrievalCoverageComparisonView = {
  added: RetrievalCoverageSummaryView[];
  improved: RetrievalCoverageStatusChangeView[];
  regressed: RetrievalCoverageStatusChangeView[];
  removed: RetrievalCoverageSummaryView[];
  retained: RetrievalCoverageSummaryView[];
};

export type RetrievalQualitySignalSummaryView = {
  code: string;
  message: string;
  severity: string;
};

export type RetrievalQualitySignalComparisonView = {
  added: RetrievalQualitySignalSummaryView[];
  removed: RetrievalQualitySignalSummaryView[];
  retained: RetrievalQualitySignalSummaryView[];
};

export type RetrievalFacetComparisonView = {
  activeCount: number;
  addedValues: string[];
  baselineCount: number;
  field: string;
  label: string;
  removedValues: string[];
  retainedValues: string[];
};

export function RunComparisonQueryProfile({
  comparison,
}: {
  comparison: RunComparisonQueryProfileView;
}) {
  const before = comparison.baselineSummary.queryProfile;
  const after = comparison.activeSummary.queryProfile;
  if (!before && !after) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Query profile</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-1 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Query profile</span>
        <Badge variant={comparison.queryProfileChanged ? "warning" : "success"}>
          {comparison.queryProfileChanged ? "changed" : "stable"}
        </Badge>
      </div>
      <div className="grid gap-1 sm:grid-cols-2">
        <QueryProfileSummaryCard label="Baseline" profile={before} />
        <QueryProfileSummaryCard label="Active" profile={after} />
      </div>
    </div>
  );
}

function QueryProfileSummaryCard({
  label,
  profile,
}: {
  label: string;
  profile: QueryProfileSummaryView | null;
}) {
  if (!profile) {
    return (
      <div className="rounded-md bg-muted/40 px-2 py-1.5 text-muted-foreground">
        {label}: unavailable
      </div>
    );
  }
  return (
    <div className="grid gap-1 rounded-md bg-muted/40 px-2 py-1.5">
      <span className="font-bold">{label}</span>
      <span className="break-words">{profile.label}</span>
      <span className="break-words text-muted-foreground">
        {humanize(profile.route)} / {humanize(profile.retrievalMode)} /{" "}
        {humanize(profile.complexity)}
      </span>
    </div>
  );
}

export function RunComparisonConceptGrounding({
  comparison,
}: {
  comparison: RetrievalConceptGroundingComparisonView;
}) {
  const changed = comparison.added.length || comparison.removed.length;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Concept grounding</span>
        <Badge variant={changed ? "warning" : "success"}>
          {changed ? "changed" : "stable"}
        </Badge>
      </div>
      <ConceptGroundingChangeList
        concepts={comparison.added}
        emptyLabel="No newly grounded concepts."
        label="Added"
        variant="success"
      />
      <ConceptGroundingChangeList
        concepts={comparison.removed}
        emptyLabel="No lost grounded concepts."
        label="Removed"
        variant="warning"
      />
      <ConceptGroundingChangeList
        concepts={comparison.retained}
        emptyLabel="No retained grounded concepts."
        label="Retained"
        variant="muted"
      />
    </div>
  );
}

function ConceptGroundingChangeList({
  concepts,
  emptyLabel,
  label,
  variant,
}: {
  concepts: ConceptGroundingSummaryView[];
  emptyLabel: string;
  label: string;
  variant: BadgeVariant;
}) {
  return (
    <div className="grid gap-1">
      <span className="font-bold text-muted-foreground">{label}</span>
      {concepts.length ? (
        <div className="flex min-w-0 flex-wrap gap-1">
          {concepts.map((concept) => (
            <Badge
              className="max-w-full break-words"
              key={conceptGroundingKey(concept)}
              variant={variant}
            >
              {concept.standardSystem}
              {concept.code ? ` ${concept.code}` : ""}: {concept.displayName} (
              {concept.evidenceCount})
            </Badge>
          ))}
        </div>
      ) : (
        <span className="text-muted-foreground">{emptyLabel}</span>
      )}
    </div>
  );
}

export function RunComparisonQueryAspects({
  comparison,
  formatCount,
}: {
  comparison: RetrievalQueryAspectComparisonView;
  formatCount: (count: number, singular: string) => string;
}) {
  const changed = comparison.added.length + comparison.removed.length;
  const total = changed + comparison.retained.length;
  if (!total) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Search aspects</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Search aspects</span>
        <Badge variant={changed ? "warning" : "success"}>
          {changed ? formatCount(changed, "changed aspect") : "stable"}
        </Badge>
      </div>
      <QueryAspectChangeList
        aspects={comparison.added}
        label="Added"
        variant="warning"
      />
      <QueryAspectChangeList
        aspects={comparison.removed}
        label="Removed"
        variant="warning"
      />
      <QueryAspectChangeList
        aspects={comparison.retained}
        label="Retained"
        variant="muted"
      />
    </div>
  );
}

function QueryAspectChangeList({
  aspects,
  label,
  variant,
}: {
  aspects: QueryAspectSummaryView[];
  label: string;
  variant: "warning" | "muted";
}) {
  if (!aspects.length) return null;
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <span className="font-semibold text-muted-foreground">{label}:</span>
        {aspects.slice(0, 4).map((aspect) => (
          <Badge key={`${label}-${aspect.aspectId}`} variant={variant}>
            {aspect.label}
          </Badge>
        ))}
        {aspects.length > 4 ? <Badge variant="muted">+{aspects.length - 4}</Badge> : null}
      </div>
      <div className="grid gap-1">
        {aspects.slice(0, 2).map((aspect) => (
          <div className="break-words text-muted-foreground" key={`${label}-${aspect.aspectId}-question`}>
            {aspect.question}
          </div>
        ))}
      </div>
    </div>
  );
}

export function RunComparisonCoverage({
  comparison,
  formatCount,
}: {
  comparison: RetrievalCoverageComparisonView;
  formatCount: (count: number, singular: string) => string;
}) {
  const changed =
    comparison.added.length +
    comparison.removed.length +
    comparison.improved.length +
    comparison.regressed.length;
  const total = changed + comparison.retained.length;
  if (!total) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Coverage diagnostics</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Coverage diagnostics</span>
        <Badge variant={comparison.regressed.length || comparison.added.length ? "warning" : "success"}>
          {changed ? formatCount(changed, "changed item") : "stable"}
        </Badge>
      </div>
      <CoverageStatusChangeList
        changes={comparison.improved}
        label="Improved"
        variant="success"
      />
      <CoverageStatusChangeList
        changes={comparison.regressed}
        label="Regressed"
        variant="warning"
      />
      <CoverageSummaryList
        items={comparison.added}
        label="Added"
        variant="warning"
      />
      <CoverageSummaryList
        items={comparison.removed}
        label="Removed"
        variant="muted"
      />
      <CoverageSummaryList
        items={comparison.retained}
        label="Retained"
        variant="muted"
      />
    </div>
  );
}

function CoverageStatusChangeList({
  changes,
  label,
  variant,
}: {
  changes: RetrievalCoverageStatusChangeView[];
  label: string;
  variant: "success" | "warning";
}) {
  if (!changes.length) return null;
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <span className="font-semibold text-muted-foreground">{label}:</span>
        {changes.slice(0, 4).map((change) => (
          <Badge key={`${label}-${coverageComparisonKey(change.active)}`} variant={variant}>
            {change.active.label}
          </Badge>
        ))}
        {changes.length > 4 ? <Badge variant="muted">+{changes.length - 4}</Badge> : null}
      </div>
      <div className="grid gap-1">
        {changes.slice(0, 2).map((change) => (
          <div
            className="break-words text-muted-foreground"
            key={`${label}-${coverageComparisonKey(change.active)}-detail`}
          >
            {humanize(change.baseline.status)} to {humanize(change.active.status)} /{" "}
            {change.baseline.selectedCount} to {change.active.selectedCount}
          </div>
        ))}
      </div>
    </div>
  );
}

function CoverageSummaryList({
  items,
  label,
  variant,
}: {
  items: RetrievalCoverageSummaryView[];
  label: string;
  variant: "warning" | "muted";
}) {
  if (!items.length) return null;
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-1.5">
      <span className="font-semibold text-muted-foreground">{label}:</span>
      {items.slice(0, 4).map((item) => (
        <Badge key={`${label}-${coverageComparisonKey(item)}`} variant={variant}>
          {item.label} / {humanize(item.status)}
        </Badge>
      ))}
      {items.length > 4 ? <Badge variant="muted">+{items.length - 4}</Badge> : null}
    </div>
  );
}

export function RunComparisonQualitySignals({
  comparison,
  formatCount,
}: {
  comparison: RetrievalQualitySignalComparisonView;
  formatCount: (count: number, singular: string) => string;
}) {
  const changed = comparison.added.length + comparison.removed.length;
  const total = changed + comparison.retained.length;
  if (!total) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Quality signals</span>
        <Badge variant="success">none</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="font-bold text-muted-foreground">Quality signals</span>
        <Badge variant={changed ? "warning" : "success"}>
          {changed ? formatCount(changed, "changed signal") : "stable"}
        </Badge>
      </div>
      <QualitySignalChangeList
        label="Added"
        signals={comparison.added}
        variant="warning"
      />
      <QualitySignalChangeList
        label="Removed"
        signals={comparison.removed}
        variant="success"
      />
      <QualitySignalChangeList
        label="Retained"
        signals={comparison.retained}
        variant="muted"
      />
    </div>
  );
}

function QualitySignalChangeList({
  label,
  signals,
  variant,
}: {
  label: string;
  signals: RetrievalQualitySignalSummaryView[];
  variant: BadgeVariant;
}) {
  if (!signals.length) return null;
  return (
    <div className="grid gap-1">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <span className="font-semibold text-muted-foreground">{label}:</span>
        {signals.slice(0, 4).map((signal) => (
          <Badge key={`${label}-${signal.code}`} variant={variant}>
            {humanize(signal.code)}
          </Badge>
        ))}
        {signals.length > 4 ? <Badge variant="muted">+{signals.length - 4}</Badge> : null}
      </div>
      <div className="grid gap-1">
        {signals.slice(0, 2).map((signal) => (
          <div className="break-words text-muted-foreground" key={`${label}-${signal.code}-message`}>
            {humanize(signal.severity)}: {signal.message}
          </div>
        ))}
      </div>
    </div>
  );
}

export function RunComparisonFacetCoverage({
  facetComparisons,
  formatCount,
}: {
  facetComparisons: RetrievalFacetComparisonView[];
  formatCount: (count: number, singular: string) => string;
}) {
  if (!facetComparisons.length) {
    return (
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2">
        <span className="text-xs font-bold text-muted-foreground">Facet coverage</span>
        <Badge variant="muted">not reported</Badge>
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs">
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

function conceptGroundingKey(concept: ConceptGroundingSummaryView) {
  return `${concept.standardSystem}:${concept.code ?? concept.conceptId}`;
}

function coverageComparisonKey(item: RetrievalCoverageSummaryView) {
  return `${item.field}:${item.value}:${item.status}`;
}
