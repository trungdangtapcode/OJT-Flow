import { Input } from "../../../components/ui/form";
import { Notice } from "../../../components/ui/notice";
import type { RetrievalSearchPreset } from "../../../types";
import { SearchPresetCard } from "./search-preset-card";
import { SearchPresetCategoryFilter } from "./search-preset-category-filter";
import { SearchPresetHeader } from "./search-preset-header";
import { useSearchPresetStripState } from "./use-search-preset-strip-state";

export function SearchPresetStrip({
  activePresetId,
  isLoading,
  onApplyPreset,
  presets,
}: {
  activePresetId: string | null;
  isLoading: boolean;
  onApplyPreset: (preset: RetrievalSearchPreset) => void;
  presets: RetrievalSearchPreset[];
}) {
  const {
    categories,
    categoryFilter,
    filteredPresets,
    presetSearch,
    setCategoryFilter,
    setPresetSearch,
  } = useSearchPresetStripState(presets);

  if (isLoading) {
    return (
      <div className="rounded-md border border-border bg-muted/20 px-3 py-2 text-sm font-semibold text-muted-foreground">
        Loading retrieval presets
      </div>
    );
  }

  if (!presets.length) {
    return (
      <Notice title="No retrieval presets">
        Add presets under the trusted knowledge directory to seed the query builder.
      </Notice>
    );
  }

  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <SearchPresetHeader
        filteredCount={filteredPresets.length}
        totalCount={presets.length}
      />
      <div className="grid gap-2">
        <Input
          aria-label="Filter retrieval presets"
          onChange={(event) => setPresetSearch(event.target.value)}
          placeholder="Filter presets"
          value={presetSearch}
        />
        <SearchPresetCategoryFilter
          activeCategory={categoryFilter}
          categories={categories}
          onSelectCategory={setCategoryFilter}
        />
      </div>
      <div className="grid gap-2">
        {filteredPresets.length ? null : (
          <Notice title="No matching presets">
            Adjust the preset filter or category to show trusted retrieval examples.
          </Notice>
        )}
        {filteredPresets.map((preset) => (
          <SearchPresetCard
            active={activePresetId === preset.preset_id}
            key={preset.preset_id}
            onApplyPreset={onApplyPreset}
            preset={preset}
          />
        ))}
      </div>
    </div>
  );
}
