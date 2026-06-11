import * as React from "react";

import type { RetrievalSearchPreset } from "../../../types";
import {
  filterSearchPresets,
  uniquePresetCategories,
} from "../model/search-preset-filter";

export function useSearchPresetStripState(presets: RetrievalSearchPreset[]) {
  const [categoryFilter, setCategoryFilter] = React.useState<string | null>(null);
  const [presetSearch, setPresetSearch] = React.useState("");
  const categories = uniquePresetCategories(presets);
  const filteredPresets = filterSearchPresets({
    category: categoryFilter,
    presets,
    search: presetSearch,
  });

  return {
    categories,
    categoryFilter,
    filteredPresets,
    presetSearch,
    setCategoryFilter,
    setPresetSearch,
  };
}
