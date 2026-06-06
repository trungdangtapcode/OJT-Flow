import { ListFilter, ShieldCheck } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { humanize } from "../../../lib/utils";
import type {
  RetrievalStandardSearchPlan,
  RetrievalStandardSearchStep,
  RetrievalStrategyRecommendation,
} from "../../../types";

export type SearchPlanFilterField =
  | "clinical_domain"
  | "standard_system"
  | "source_type"
  | "trust_level"
  | "source_id";

export type SearchPlanFilterAction = {
  field: SearchPlanFilterField;
  value: string;
};

export function StrategyRecommendationsPanel({
  getSuggestedFilterAction,
  isSearchPending,
  onApplyFilter,
  recommendations,
}: {
  getSuggestedFilterAction: (value: unknown) => SearchPlanFilterAction | null;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
  recommendations: RetrievalStrategyRecommendation[];
}) {
  if (!recommendations.length) {
    return null;
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
          Strategy recommendations
          <HelpTooltip label="Strategy recommendations help">
            Backend-generated search advice. Apply a recommendation only when it matches the operational question and the suggested filter is supported.
          </HelpTooltip>
        </div>
        <Badge variant="muted">{formatCount(recommendations.length, "rule")}</Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        {recommendations.slice(0, 4).map((recommendation) => (
          <StrategyRecommendationCard
            getSuggestedFilterAction={getSuggestedFilterAction}
            isSearchPending={isSearchPending}
            key={recommendation.recommendation_id}
            onApplyFilter={onApplyFilter}
            recommendation={recommendation}
          />
        ))}
      </div>
    </div>
  );
}

export function StandardSearchPlanPanel({
  getSuggestedFilterAction,
  isSearchPending,
  onApplyFilter,
  plan,
}: {
  getSuggestedFilterAction: (value: unknown) => SearchPlanFilterAction | null;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
  plan: RetrievalStandardSearchPlan | null;
}) {
  if (!plan || !plan.steps.length) {
    return null;
  }
  const visibleNotes = plan.governance_notes.slice(0, 3);
  return (
    <div className="grid gap-3 rounded-md border border-border bg-card p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase text-muted-foreground">
            Healthcare search plan
            <HelpTooltip label="Healthcare search plan help">
              Backend-selected playbook for the next standards-aware search. It maps the query to FHIR, terminology, privacy, or external medical-search routes before downstream use.
            </HelpTooltip>
          </div>
          <div className="mt-1 break-words text-sm leading-6 text-muted-foreground">
            {plan.summary}
          </div>
        </div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={standardRouteBadgeVariant(plan.primary_route)}>
            {humanize(plan.primary_route)}
          </Badge>
          <Badge variant="muted">{formatCount(plan.steps.length, "step")}</Badge>
          {plan.missing_routes.length ? (
            <Badge variant="warning">
              {formatCount(plan.missing_routes.length, "missing route")}
            </Badge>
          ) : null}
        </div>
      </div>
      <div className="grid gap-2 lg:grid-cols-2">
        {plan.steps.slice(0, 4).map((step) => (
          <StandardSearchStepCard
            getSuggestedFilterAction={getSuggestedFilterAction}
            isSearchPending={isSearchPending}
            key={step.step_id}
            onApplyFilter={onApplyFilter}
            step={step}
          />
        ))}
      </div>
      {visibleNotes.length ? (
        <div className="grid gap-1 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-950">
          <div className="font-black uppercase">Governance guardrails</div>
          <ul className="grid gap-1">
            {visibleNotes.map((note) => (
              <li className="grid grid-cols-[12px_minmax(0,1fr)] gap-2" key={note}>
                <span aria-hidden="true" className="pt-0.5 font-black">
                  -
                </span>
                <span className="min-w-0 break-words">{note}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function StandardSearchStepCard({
  getSuggestedFilterAction,
  isSearchPending,
  onApplyFilter,
  step,
}: {
  getSuggestedFilterAction: (value: unknown) => SearchPlanFilterAction | null;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
  step: RetrievalStandardSearchStep;
}) {
  const filterAction = getSuggestedFilterAction(step.suggested_filters);
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
      <div className="grid min-w-0 gap-2 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
        <div className="min-w-0">
          <div className="break-words font-black">{step.label}</div>
          <div className="mt-1 flex min-w-0 flex-wrap items-center gap-1.5">
            <Badge variant="muted">P{step.priority}</Badge>
            <Badge variant="success">{step.standard_system}</Badge>
            <Badge variant={standardRouteBadgeVariant(step.route_type)}>
              {humanize(step.route_type)}
            </Badge>
          </div>
        </div>
        {filterAction ? (
          <Button
            disabled={isSearchPending}
            onClick={() => onApplyFilter(filterAction.field, filterAction.value)}
            size="sm"
            type="button"
            variant="outline"
          >
            <ListFilter className="h-4 w-4" />
            Apply {filterFieldLabel(filterAction.field)}
          </Button>
        ) : null}
      </div>
      <div className="break-words text-xs leading-5 text-muted-foreground">
        {step.rationale}
      </div>
      <StandardSearchMatchReasons metadata={step.metadata} />
      <div className="break-words rounded-md border border-border bg-card px-3 py-2 font-mono text-xs leading-5 text-foreground">
        {step.query}
      </div>
      <StandardSearchGovernanceNotes notes={step.governance_notes} />
    </div>
  );
}

function StandardSearchMatchReasons({ metadata }: { metadata: Record<string, unknown> }) {
  const reasons = standardSearchMatchReasons(metadata);
  if (!reasons.length) {
    return null;
  }
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-1.5 text-xs">
      <span className="font-black uppercase text-muted-foreground">Matched by</span>
      {reasons.map((reason) => (
        <Badge key={`${reason.label}:${reason.value}`} variant={reason.variant}>
          {reason.label}: {reason.value}
        </Badge>
      ))}
    </div>
  );
}

function StandardSearchGovernanceNotes({ notes }: { notes: string[] }) {
  const visibleNotes = notes.slice(0, 2);
  if (!visibleNotes.length) {
    return null;
  }
  return (
    <div className="grid gap-1 text-xs leading-5 text-muted-foreground">
      {visibleNotes.map((note) => (
        <div className="grid grid-cols-[14px_minmax(0,1fr)] gap-2" key={note}>
          <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-700" />
          <span className="min-w-0 break-words">{note}</span>
        </div>
      ))}
    </div>
  );
}

function StrategyRecommendationCard({
  getSuggestedFilterAction,
  isSearchPending,
  onApplyFilter,
  recommendation,
}: {
  getSuggestedFilterAction: (value: unknown) => SearchPlanFilterAction | null;
  isSearchPending: boolean;
  onApplyFilter: (field: SearchPlanFilterField, value: string) => void;
  recommendation: RetrievalStrategyRecommendation;
}) {
  const filterAction = getSuggestedFilterAction(recommendation.suggested_filters);
  return (
    <div className="grid gap-1 rounded-md border border-border bg-muted/20 px-3 py-2 text-sm">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <Badge variant={strategyRecommendationVariant(recommendation.status)}>
          {humanize(recommendation.status)}
        </Badge>
        <span className="break-words font-black">{recommendation.title}</span>
      </div>
      <div className="break-words text-xs font-semibold text-muted-foreground">
        {humanize(recommendation.technique)}
      </div>
      <div className="break-words text-xs leading-5 text-muted-foreground">
        {recommendation.rationale}
      </div>
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        {recommendation.source_signal_codes.slice(0, 3).map((code) => (
          <Badge key={code} variant="muted">
            {humanize(code)}
          </Badge>
        ))}
        {filterAction ? (
          <Button
            disabled={isSearchPending}
            onClick={() => onApplyFilter(filterAction.field, filterAction.value)}
            size="sm"
            type="button"
            variant="outline"
          >
            <ListFilter className="h-4 w-4" />
            Apply {filterFieldLabel(filterAction.field)}
          </Button>
        ) : null}
      </div>
    </div>
  );
}

function standardSearchMatchReasons(metadata: Record<string, unknown>) {
  const sources: {
    key: string;
    label: string;
    variant: React.ComponentProps<typeof Badge>["variant"];
  }[] = [
    { key: "matched_fields", label: "field", variant: "default" },
    { key: "matched_query_aspects", label: "aspect", variant: "muted" },
    { key: "matched_standards", label: "standard", variant: "success" },
    { key: "matched_concepts", label: "concept", variant: "muted" },
    { key: "source_quality_signal_codes", label: "signal", variant: "warning" },
  ];
  return sources.flatMap((source) =>
    stringArrayValue(metadata[source.key])
      .slice(0, 3)
      .map((value) => ({
        label: source.label,
        value,
        variant: source.variant,
      })),
  );
}

function standardRouteBadgeVariant(
  routeType: string,
): "default" | "success" | "warning" | "destructive" | "muted" {
  const normalized = routeType.toLowerCase();
  if (normalized.includes("privacy") || normalized.includes("review")) return "warning";
  if (normalized.includes("fhir") || normalized.includes("terminology")) return "default";
  if (normalized.includes("validation")) return "success";
  if (normalized.includes("external")) return "muted";
  return "muted";
}

function strategyRecommendationVariant(status: string) {
  if (status === "active") return "success";
  if (status === "action_required" || status === "caution") return "warning";
  return "muted";
}

function filterFieldLabel(field: SearchPlanFilterField): string {
  if (field === "clinical_domain") return "Domain";
  if (field === "source_id") return "Source ID";
  if (field === "standard_system") return "Standard";
  if (field === "source_type") return "Source";
  return "Trust";
}

function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.length > 0);
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
