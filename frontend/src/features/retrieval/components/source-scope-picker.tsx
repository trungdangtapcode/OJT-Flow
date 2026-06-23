import { X } from "lucide-react";

import { Input } from "../../../components/ui/form";
import { SourceScopeEmptyState } from "./source-scope-empty-state";
import { SourceScopeOptionRow } from "./source-scope-option-row";
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
    <div className="grid gap-2">
      <div className="flex min-w-0 items-center justify-between gap-2">
        <span className="text-xs font-semibold text-muted-foreground">
          Source scope {sourceId ? `— ${selectedSource?.title ?? sourceId}` : ""}
        </span>
        {sourceId ? (
          <button
            className="text-[11px] font-medium text-muted-foreground hover:text-foreground disabled:opacity-50"
            disabled={isSearchPending}
            onClick={onClear}
            type="button"
          >
            <X className="inline h-3 w-3" /> Clear
          </button>
        ) : null}
      </div>
      <SourceScopeStatusNotice sourceId={sourceId} />
      {sourceId ? (
        <SourceScopeSelectedSummary selectedSource={selectedSource} sourceId={sourceId} />
      ) : null}
      <Input
        aria-label="Search sources"
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Filter sources..."
        value={search}
      />
      <div className="grid gap-1">
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
