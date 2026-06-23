import { Input } from "../../../components/ui/form";
import type { RetrievalSearchPreset } from "../../../types";
import { SearchPresetCard } from "./search-preset-card";
import { SearchPresetCategoryFilter } from "./search-preset-category-filter";
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

  if (isLoading || !presets.length) return null;

  return (
    <div className="grid gap-2">
      <div className="flex items-center gap-2">
        <Input
          aria-label="Filter presets"
          className="h-7 text-xs"
          onChange={(event) => setPresetSearch(event.target.value)}
          placeholder="Filter presets..."
          value={presetSearch}
        />
        <SearchPresetCategoryFilter
          activeCategory={categoryFilter}
          categories={categories}
          onSelectCategory={setCategoryFilter}
        />
      </div>
      <div className="grid gap-1.5 sm:grid-cols-2">
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
