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

      <SearchPresetStrip
        activePresetId={value.activePresetId}
        isLoading={status.presetsLoading}
        onApplyPreset={actions.onApplyPreset}
        presets={options.presets}
      />

      <QueryBuilderTextFields actions={actions} value={value} />
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

      <QueryBuilderActiveFilterBar actions={actions} value={value} />

      <QueryBuilderSubmitButton isSearchPending={value.isSearchPending} />
    </>
  );
}
