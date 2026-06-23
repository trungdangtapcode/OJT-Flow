import { SlidersHorizontal } from "lucide-react";

import { QueryBuilderActiveFilterBar } from "./query-builder-active-filter-bar";
import {
  QueryBuilderContextFields,
  QueryBuilderScopeFields,
  QueryBuilderTextFields,
} from "./query-builder-fields";
import { QueryBuilderNotices } from "./query-builder-notices";
import type {
  RetrievalQueryBuilderActions,
  RetrievalQueryBuilderOptions,
  RetrievalQueryBuilderStatus,
  RetrievalQueryBuilderValue,
} from "./query-builder-panel-types";
import { QueryBuilderSubmitButton } from "./query-builder-submit-button";
import { SearchPresetStrip } from "./search-preset-strip";
import { SourceScopePicker } from "./source-scope-picker";

export function QueryBuilderFormContent({
  actions,
  options,
  status,
  value,
}: {
  actions: RetrievalQueryBuilderActions;
  options: RetrievalQueryBuilderOptions;
  status: RetrievalQueryBuilderStatus;
  value: RetrievalQueryBuilderValue;
}) {
  return (
    <>
      <QueryBuilderNotices
        formError={value.formError}
        isSearchResultStale={value.isSearchResultStale}
        planControlNotice={value.planControlNotice}
        presetsError={status.presetsError}
        searchError={status.searchError}
        searchOptionsError={status.searchOptionsError}
      />

      <QueryBuilderTextFields actions={actions} value={value} />

      <div className="flex items-center gap-2">
        <QueryBuilderSubmitButton isSearchPending={value.isSearchPending} />
        <QueryBuilderActiveFilterBar actions={actions} value={value} />
      </div>

      <details className="rounded-lg border border-border/40 bg-muted/10 px-3 py-2">
        <summary className="flex cursor-pointer list-none items-center gap-2 text-xs font-medium text-muted-foreground">
          <SlidersHorizontal className="h-3.5 w-3.5" />
          Filters &amp; presets
        </summary>
        <div className="mt-3 grid gap-3">
          <SearchPresetStrip
            activePresetId={value.activePresetId}
            isLoading={status.presetsLoading}
            onApplyPreset={actions.onApplyPreset}
            presets={options.presets}
          />

          <QueryBuilderContextFields actions={actions} options={options} value={value} />
          <QueryBuilderScopeFields actions={actions} options={options} value={value} />

          <SourceScopePicker
            isSearchPending={value.isSearchPending}
            onClear={actions.onClearSourceScope}
            onSelect={actions.onSelectSourceScope}
            selectedSource={options.selectedSource}
            sourceId={value.sourceId}
            sources={options.sources}
          />
        </div>
      </details>
    </>
  );
}
