import * as React from "react";
import { Search, X } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { Input } from "../../../components/ui/form";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { cn, humanize } from "../../../lib/utils";
import type { RetrievalSource } from "../../../types";
import { SourceReadinessMetric } from "./metric-primitives";
import { SectionHelpText } from "./section-help-text";

type SourceInventoryReadiness = {
  chunkCount: number;
  domainCount: number;
  emptySourceCount: number;
  filteredCount: number;
  readiness: "ready" | "review" | "blocked";
  standardCount: number;
  sourceCount: number;
  sourceTypeCount: number;
};

export function SourceInventoryPanel({
  isLoading,
  onUseSource,
  sources,
}: {
  isLoading: boolean;
  onUseSource: (sourceId: string) => void;
  sources: RetrievalSource[];
}) {
  const [sourceSearch, setSourceSearch] = React.useState("");
  const [sourceTypeFilter, setSourceTypeFilter] = React.useState<string | null>(null);
  const [sourceDomainFilter, setSourceDomainFilter] = React.useState<string | null>(null);
  const [sourceStandardFilter, setSourceStandardFilter] = React.useState<string | null>(null);
  const filteredSources = sources.filter((source) =>
    sourceMatchesInventoryFilters(source, {
      domain: sourceDomainFilter,
      search: sourceSearch,
      standard: sourceStandardFilter,
      type: sourceTypeFilter,
    }),
  );
  const sourceTypeOptions = uniqueValues(sources.map((source) => source.source_type));
  const sourceDomainOptions = uniqueValues(sources.map((source) => source.clinical_domain));
  const sourceStandardOptions = uniqueValues(sources.map((source) => source.standard_system));
  const hasSourceFilters = Boolean(
    sourceSearch.trim() ||
      sourceTypeFilter ||
      sourceDomainFilter ||
      sourceStandardFilter,
  );
  const readiness = sourceInventoryReadiness(sources, filteredSources);
  const clearSourceFilters = () => {
    setSourceSearch("");
    setSourceTypeFilter(null);
    setSourceDomainFilter(null);
    setSourceStandardFilter(null);
  };

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="flex-row flex-wrap items-start justify-between gap-3 border-b border-border bg-card/70">
        <div className="min-w-0">
          <CardTitle className="flex items-center gap-2">
            Trusted sources
            <HelpTooltip label="Trusted sources help">
              Source inventory shows what the retrieval system can search. The Use source action applies exact source scope to the query builder.
            </HelpTooltip>
          </CardTitle>
          <CardDescription>
            {isLoading
              ? "Loading inventory"
              : `${formatCount(filteredSources.length, "source")} shown from ${sources.length}`}
          </CardDescription>
        </div>
        {hasSourceFilters ? (
          <Button onClick={clearSourceFilters} size="sm" type="button" variant="outline">
            <X className="h-4 w-4" />
            Clear filters
          </Button>
        ) : null}
      </CardHeader>
      <CardContent className="grid gap-3 pt-4">
        <SectionHelpText>
          Inventory filters only inspect available sources. Use source constrains retrieval to one source ID; clear exact source scope for corpus-wide coverage.
        </SectionHelpText>
        <SourceInventoryReadinessPanel
          hasSourceFilters={hasSourceFilters}
          readiness={readiness}
        />
        <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
              Source inventory filters
              <HelpTooltip label="Source inventory filters help">
                Inventory filters inspect available trusted sources. Use source scope only when you intentionally want evidence from one exact source.
              </HelpTooltip>
            </div>
            <Badge variant="muted">
              {filteredSources.length}/{sources.length}
            </Badge>
          </div>
          <Input
            aria-label="Filter trusted sources"
            onChange={(event) => setSourceSearch(event.target.value)}
            placeholder="Filter sources by title, ID, type, domain, or standard"
            value={sourceSearch}
          />
          <SourceFilterChips
            activeValue={sourceTypeFilter}
            formatter={humanize}
            label="Source type"
            onSelect={setSourceTypeFilter}
            values={sourceTypeOptions}
          />
          <SourceFilterChips
            activeValue={sourceDomainFilter}
            formatter={humanize}
            label="Domain"
            onSelect={setSourceDomainFilter}
            values={sourceDomainOptions}
          />
          <SourceFilterChips
            activeValue={sourceStandardFilter}
            formatter={(value) => value}
            label="Standard"
            onSelect={setSourceStandardFilter}
            values={sourceStandardOptions}
          />
        </div>
        <div className="grid gap-3">
          {filteredSources.map((source) => (
            <SourceCard key={source.source_id} onUseSource={onUseSource} source={source} />
          ))}
          {!filteredSources.length ? (
            <div className="rounded-md border border-border p-3 text-sm text-muted-foreground">
              {isLoading
                ? "Loading sources."
                : hasSourceFilters
                  ? "No sources match the current filters."
                  : "No retrieval sources indexed."}
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

function SourceFilterChips({
  activeValue,
  formatter,
  label,
  onSelect,
  values,
}: {
  activeValue: string | null;
  formatter: (value: string) => string;
  label: string;
  onSelect: (value: string | null) => void;
  values: string[];
}) {
  if (!values.length) return null;
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold text-muted-foreground">{label}</div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <button
          aria-pressed={!activeValue}
          className={sourceFilterChipClass(!activeValue)}
          onClick={() => onSelect(null)}
          type="button"
        >
          All
        </button>
        {values.map((value) => {
          const active = activeValue === value;
          return (
            <button
              aria-pressed={active}
              className={sourceFilterChipClass(active)}
              key={value}
              onClick={() => onSelect(value)}
              type="button"
            >
              {formatter(value)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function SourceInventoryReadinessPanel({
  hasSourceFilters,
  readiness,
}: {
  hasSourceFilters: boolean;
  readiness: SourceInventoryReadiness;
}) {
  const blocked = readiness.readiness === "blocked";
  const review = readiness.readiness === "review";
  return (
    <div
      aria-label="Source inventory readiness"
      className={cn(
        "grid gap-2 rounded-md border p-3",
        blocked
          ? "border-red-200 bg-red-50 text-red-950"
          : review
            ? "border-amber-200 bg-amber-50 text-amber-950"
            : "border-emerald-200 bg-emerald-50 text-emerald-950",
      )}
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-black uppercase">
          Source readiness
          <HelpTooltip label="Source readiness help">
            Summarizes whether the trusted corpus has searchable sources, chunks, domains, and standards before you apply exact source scope.
          </HelpTooltip>
        </div>
        <Badge variant={sourceInventoryReadinessVariant(readiness.readiness)}>
          {humanize(readiness.readiness)}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <SourceReadinessMetric label="Sources" value={`${readiness.filteredCount}/${readiness.sourceCount}`} />
        <SourceReadinessMetric label="Chunks" value={formatCount(readiness.chunkCount, "chunk")} />
        <SourceReadinessMetric label="Domains" value={formatCount(readiness.domainCount, "domain")} />
        <SourceReadinessMetric label="Standards" value={formatCount(readiness.standardCount, "standard")} />
      </div>
      <div className="break-words text-sm font-semibold leading-6">
        {sourceInventoryReadinessMessage(readiness, hasSourceFilters)}
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <Badge variant={readiness.sourceTypeCount ? "success" : "warning"}>
          {formatCount(readiness.sourceTypeCount, "source type")}
        </Badge>
        <Badge variant={readiness.emptySourceCount ? "warning" : "success"}>
          {readiness.emptySourceCount
            ? formatCount(readiness.emptySourceCount, "empty source")
            : "all shown sources have chunks"}
        </Badge>
        {hasSourceFilters ? <Badge variant="warning">filtered inventory</Badge> : null}
      </div>
    </div>
  );
}

function SourceCard({
  onUseSource,
  source,
}: {
  onUseSource: (sourceId: string) => void;
  source: RetrievalSource;
}) {
  return (
    <article className="grid gap-2 rounded-md border border-border bg-muted/20 p-3 text-sm">
      <div className="min-w-0">
        <div className="break-words font-bold">{source.title}</div>
        <div className="break-all font-mono text-xs text-muted-foreground">
          {source.source_id}
        </div>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
          {humanize(source.source_type)}
        </span>
        {source.clinical_domain ? (
          <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
            {humanize(source.clinical_domain)}
          </span>
        ) : null}
        {source.standard_system ? (
          <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
            {source.standard_system}
          </span>
        ) : null}
        <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
          {formatCount(source.chunk_count, "chunk")}
        </span>
      </div>
      <Button
        className="w-fit"
        onClick={() => onUseSource(source.source_id)}
        size="sm"
        type="button"
        variant="outline"
      >
        <Search className="h-4 w-4" />
        Use source
      </Button>
    </article>
  );
}

function sourceInventoryReadiness(
  sources: RetrievalSource[],
  filteredSources: RetrievalSource[],
): SourceInventoryReadiness {
  const chunkCount = filteredSources.reduce((count, source) => count + source.chunk_count, 0);
  const emptySourceCount = filteredSources.filter((source) => source.chunk_count <= 0).length;
  const readiness =
    !sources.length || !filteredSources.length || chunkCount <= 0
      ? "blocked"
      : emptySourceCount > 0 || filteredSources.length < sources.length
        ? "review"
        : "ready";
  return {
    chunkCount,
    domainCount: uniqueValues(filteredSources.map((source) => source.clinical_domain)).length,
    emptySourceCount,
    filteredCount: filteredSources.length,
    readiness,
    sourceCount: sources.length,
    sourceTypeCount: uniqueValues(filteredSources.map((source) => source.source_type)).length,
    standardCount: uniqueValues(filteredSources.map((source) => source.standard_system)).length,
  };
}

function sourceInventoryReadinessVariant(
  readiness: SourceInventoryReadiness["readiness"],
): "success" | "warning" | "destructive" {
  if (readiness === "ready") return "success";
  if (readiness === "review") return "warning";
  return "destructive";
}

function sourceInventoryReadinessMessage(
  readiness: SourceInventoryReadiness,
  hasSourceFilters: boolean,
): string {
  if (!readiness.sourceCount) {
    return "No trusted sources are loaded. Reindex the corpus before judging retrieval quality.";
  }
  if (!readiness.filteredCount) {
    return "No trusted sources match the current inventory filters. Clear filters before concluding the corpus lacks coverage.";
  }
  if (!readiness.chunkCount) {
    return "Matching sources have no indexed chunks. Refresh or reindex before relying on retrieval results.";
  }
  if (hasSourceFilters) {
    return "Inventory is filtered. Use this view to inspect available source types, but clear filters for corpus-wide coverage checks.";
  }
  if (readiness.emptySourceCount) {
    return "Some trusted sources have no indexed chunks. Review index integrity before using exact source scope.";
  }
  return "Trusted source inventory is searchable. Use exact source scope only for audit or source-specific debugging.";
}

function sourceFilterChipClass(active: boolean) {
  return cn(
    "rounded-full border px-2.5 py-1 text-xs font-bold transition-colors",
    active
      ? "border-primary bg-primary/10 text-primary"
      : "border-border bg-background text-muted-foreground hover:bg-muted",
  );
}

function sourceMatchesInventoryFilters(
  source: RetrievalSource,
  filters: {
    domain: string | null;
    search: string;
    standard: string | null;
    type: string | null;
  },
) {
  if (filters.type && source.source_type !== filters.type) return false;
  if (filters.domain && source.clinical_domain !== filters.domain) return false;
  if (filters.standard && source.standard_system !== filters.standard) return false;

  const normalizedSearch = filters.search.trim().toLowerCase();
  if (!normalizedSearch) return true;
  return [
    source.source_id,
    source.title,
    source.source_type,
    source.clinical_domain,
    source.standard_system,
    source.source_version,
    source.trust_level,
  ].some((value) => value?.toLowerCase().includes(normalizedSearch));
}

function uniqueValues(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort();
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
