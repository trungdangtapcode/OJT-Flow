import { X } from "lucide-react";

import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/form";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { SourceScopeEmptyState } from "./source-scope-empty-state";
import { SourceScopeOptionRow } from "./source-scope-option-row";
import {
  formatSourceCount,
} from "./source-scope-picker-format";
import type { SourceScopePickerProps } from "./source-scope-picker-types";
import { SourceScopeSelectedSummary } from "./source-scope-selected-summary";
import { SourceScopeStatusNotice } from "./source-scope-status-notice";
import { useSourceScopePickerState } from "./use-source-scope-picker-state";

export function SourceScopePicker({
  isSearchPending,
  onClear,
  onSelect,
  selectedSource,
  sourceId,
  sources,
}: SourceScopePickerProps) {
  const { search, setSearch, visibleSources } = useSourceScopePickerState(sources);

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
              : `${formatSourceCount(sources.length, "approved source")} available`}
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
      <SourceScopeStatusNotice sourceId={sourceId} />
      {sourceId ? (
        <SourceScopeSelectedSummary selectedSource={selectedSource} sourceId={sourceId} />
      ) : null}
      <Input
        aria-label="Search exact source scope"
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Search source ID, title, type, domain, or standard"
        value={search}
      />
      <div className="grid gap-1.5">
        {visibleSources.map((source) => (
          <SourceScopeOptionRow
            isSearchPending={isSearchPending}
            isSelected={source.source_id === sourceId}
            key={source.source_id}
            onSelect={onSelect}
            source={source}
          />
        ))}
        {!visibleSources.length ? (
          <SourceScopeEmptyState hasSources={Boolean(sources.length)} />
        ) : null}
      </div>
    </div>
  );
}
