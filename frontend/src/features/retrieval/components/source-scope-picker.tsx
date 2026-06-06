import * as React from "react";
import { AlertTriangle, Search, X } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/form";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { cn, humanize } from "../../../lib/utils";
import type { RetrievalSource } from "../../../types";

export function SourceScopePicker({
  isSearchPending,
  onClear,
  onSelect,
  selectedSource,
  sourceId,
  sources,
}: {
  isSearchPending: boolean;
  onClear: () => void;
  onSelect: (sourceId: string) => void;
  selectedSource: RetrievalSource | null;
  sourceId: string;
  sources: RetrievalSource[];
}) {
  const [search, setSearch] = React.useState("");
  const visibleSources = sources.filter((source) => sourceMatchesSearch(source, search)).slice(0, 8);
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
            Exact source scope
            <HelpTooltip label="Exact source scope help">
              Exact source scope reruns retrieval against one source ID. Use it for audit or source-specific debugging, not broad evidence discovery.
            </HelpTooltip>
          </div>
          <div className="mt-1 break-words text-sm font-semibold text-muted-foreground">
            {sourceId
              ? selectedSource?.title ?? sourceId
              : `${formatCount(sources.length, "approved source")} available`}
          </div>
        </div>
        {sourceId ? (
          <Button
            disabled={isSearchPending}
            onClick={onClear}
            size="sm"
            type="button"
            variant="outline"
          >
            <X className="h-4 w-4" />
            Clear source
          </Button>
        ) : null}
      </div>
      <div
        className={cn(
          "flex min-w-0 items-start gap-2 rounded-md border px-3 py-2 text-xs leading-5",
          sourceId
            ? "border-amber-200 bg-amber-50 text-amber-950"
            : "border-border bg-card text-muted-foreground",
        )}
      >
        {sourceId ? (
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-700" />
        ) : (
          <Search className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
        )}
        <span className="min-w-0 break-words font-semibold">
          {sourceId
            ? "Search is constrained to one exact source. Clear it before judging corpus-wide evidence coverage."
            : "Leave exact source blank for broad search. Pick a source only when you need source-specific evidence."}
        </span>
      </div>
      {sourceId ? (
        <SelectedSourceSummary selectedSource={selectedSource} sourceId={sourceId} />
      ) : null}
      <Input
        aria-label="Search exact source scope"
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Search source ID, title, type, domain, or standard"
        value={search}
      />
      <div className="grid gap-1.5">
        {visibleSources.map((source) => (
          <button
            className={cn(
              "grid min-w-0 gap-1 rounded-md border px-3 py-2 text-left text-sm transition-colors",
              source.source_id === sourceId
                ? "border-primary bg-primary/10"
                : "border-border bg-card hover:border-primary hover:bg-primary/5",
            )}
            disabled={isSearchPending}
            key={source.source_id}
            onClick={() => onSelect(source.source_id)}
            type="button"
          >
            <span className="break-words font-bold">{source.title}</span>
            {source.source_id === sourceId ? (
              <Badge className="w-fit" variant="success">
                applied exact source
              </Badge>
            ) : null}
            <span className="break-all font-mono text-xs text-muted-foreground">
              {source.source_id}
            </span>
            <SourceMetadataBadges source={source} />
          </button>
        ))}
        {!visibleSources.length ? (
          <div className="rounded-md border border-border bg-card p-3 text-sm text-muted-foreground">
            {sources.length ? "No source matches this search." : "No retrieval sources loaded."}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function SelectedSourceSummary({
  selectedSource,
  sourceId,
}: {
  selectedSource: RetrievalSource | null;
  sourceId: string;
}) {
  return (
    <div className="grid gap-1 rounded-md border border-primary/25 bg-primary/10 p-2 text-sm">
      <div className="font-bold">{selectedSource?.title ?? sourceId}</div>
      <div className="break-all font-mono text-xs text-muted-foreground">{sourceId}</div>
      {selectedSource ? <SourceMetadataBadges source={selectedSource} /> : null}
    </div>
  );
}

function SourceMetadataBadges({ source }: { source: RetrievalSource }) {
  return (
    <span className="flex min-w-0 flex-wrap gap-1.5">
      <Badge variant="muted">{humanize(source.source_type)}</Badge>
      {source.clinical_domain ? (
        <Badge variant="muted">{humanize(source.clinical_domain)}</Badge>
      ) : null}
      {source.standard_system ? (
        <Badge variant="muted">{source.standard_system}</Badge>
      ) : null}
      <Badge variant="muted">{formatCount(source.chunk_count, "chunk")}</Badge>
    </span>
  );
}

function sourceMatchesSearch(source: RetrievalSource, search: string) {
  const normalized = search.trim().toLowerCase();
  if (!normalized) return true;
  return [
    source.source_id,
    source.title,
    source.source_type,
    source.clinical_domain,
    source.standard_system,
  ].some((value) => value?.toLowerCase().includes(normalized));
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
