import { Gauge, ListFilter, Network } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalScoreComponent } from "../../../types";

export type DiversitySelectionExplanationView = {
  originalRank: number;
  reason: string;
  redundancyScore: number;
  relevanceScore: number;
  selectedRank: number;
  selectionScore: number;
};

export type ConceptMatchExplanationView = {
  code: string | null;
  conceptId: string;
  confidence: number;
  displayName: string;
  matchedAliases: string[];
  matchedFields: string[];
  reason: string;
  standardSystem: string;
};

export type QueryAspectMatchExplanationView = {
  aspectId: string;
  label: string;
  matchedFilters: Record<string, string>;
  matchedTerms: string[];
  priority: number;
  reason: string;
  ruleId: string;
};

export function ScoreMeter({
  formatScore,
  label,
  value,
}: {
  formatScore: (value: number) => string;
  label: string;
  value: number;
}) {
  const normalized = Math.max(0, Math.min(100, Math.abs(value) * 100));
  return (
    <div className="grid gap-1 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex items-center justify-between gap-2 text-xs font-bold">
        <span>{label}</span>
        <span className="tabular-nums text-muted-foreground">{formatScore(value)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-border">
        <div className="h-full rounded-full bg-primary" style={{ width: `${normalized}%` }} />
      </div>
    </div>
  );
}

export function ScoreExplanation({
  components,
  formatScore,
}: {
  components: RetrievalScoreComponent[];
  formatScore: (value: number) => string;
}) {
  if (!components.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <Gauge className="h-3.5 w-3.5 shrink-0" />
        <span>Score explanation</span>
      </div>
      <div className="grid gap-1.5">
        {components.map((component) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs md:grid-cols-[10rem_5rem_minmax(0,1fr)] md:items-center"
            key={component.component}
          >
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <span className="min-w-0 break-words font-bold">{component.label}</span>
              {component.rank ? <Badge variant="muted">rank {component.rank}</Badge> : null}
            </div>
            <span className="font-mono font-semibold tabular-nums text-muted-foreground">
              {formatScore(component.value)}
            </span>
            <span className="min-w-0 break-words font-semibold text-muted-foreground">
              {component.description}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function DiversitySelectionExplanation({
  formatScore,
  selection,
}: {
  formatScore: (value: number) => string;
  selection: DiversitySelectionExplanationView | null;
}) {
  if (!selection) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <Network className="h-3.5 w-3.5 shrink-0" />
        <span>Diversity selection</span>
      </div>
      <div className="grid gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs">
        <div className="flex min-w-0 flex-wrap items-center gap-1.5">
          <Badge variant="muted">selected #{selection.selectedRank}</Badge>
          <Badge variant="muted">original #{selection.originalRank}</Badge>
          <span className="font-mono font-semibold text-muted-foreground">
            relevance {formatScore(selection.relevanceScore)}
          </span>
          <span className="font-mono font-semibold text-muted-foreground">
            redundancy {formatScore(selection.redundancyScore)}
          </span>
          <span className="font-mono font-semibold text-muted-foreground">
            MMR {formatScore(selection.selectionScore)}
          </span>
        </div>
        <div className="break-words font-semibold text-muted-foreground">
          {selection.reason}
        </div>
      </div>
    </div>
  );
}

export function ConceptMatchExplanation({
  matches,
}: {
  matches: ConceptMatchExplanationView[];
}) {
  if (!matches.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <Network className="h-3.5 w-3.5 shrink-0" />
        <span>Concept grounding</span>
      </div>
      <div className="grid gap-1.5">
        {matches.map((match) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs"
            key={`${match.standardSystem}-${match.conceptId}`}
          >
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <Badge className="max-w-full break-words" variant="success">
                {match.standardSystem}
                {match.code ? ` ${match.code}` : ""}
              </Badge>
              <span className="min-w-0 break-words font-bold">{match.displayName}</span>
              <span className="font-mono font-semibold text-muted-foreground">
                {Math.round(match.confidence * 100)}%
              </span>
            </div>
            <div className="break-words font-semibold text-muted-foreground">
              {match.reason}
            </div>
            <div className="flex min-w-0 flex-wrap gap-1">
              {match.matchedFields.map((field) => (
                <span
                  className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                  key={`${match.conceptId}-${field}`}
                >
                  {humanize(field)}
                </span>
              ))}
              {match.matchedAliases.slice(0, 3).map((alias) => (
                <span
                  className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                  key={`${match.conceptId}-${alias}`}
                >
                  {alias}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function QueryAspectMatchExplanation({
  matches,
}: {
  matches: QueryAspectMatchExplanationView[];
}) {
  if (!matches.length) return null;
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-2">
      <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
        <ListFilter className="h-3.5 w-3.5 shrink-0" />
        <span>Aspect support</span>
      </div>
      <div className="grid gap-1.5">
        {matches.map((match) => (
          <div
            className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs"
            key={`${match.aspectId}-${match.ruleId}`}
          >
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <Badge className="max-w-full break-words" variant="success">
                {match.label}
              </Badge>
              <Badge variant="muted">priority {match.priority}</Badge>
              <span className="min-w-0 break-words font-semibold text-muted-foreground">
                {match.reason}
              </span>
            </div>
            {match.matchedTerms.length || Object.keys(match.matchedFilters).length ? (
              <div className="flex min-w-0 flex-wrap gap-1">
                {Object.entries(match.matchedFilters).map(([field, value]) => (
                  <span
                    className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                    key={`${match.aspectId}-${field}`}
                  >
                    {humanize(field)}: {value}
                  </span>
                ))}
                {match.matchedTerms.slice(0, 4).map((term) => (
                  <span
                    className="max-w-full break-words rounded-full bg-muted px-2 py-1 font-bold text-muted-foreground"
                    key={`${match.aspectId}-${term}`}
                  >
                    {term}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
