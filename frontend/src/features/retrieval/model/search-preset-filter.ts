import type { RetrievalSearchPreset } from "../../../types";

export function filterSearchPresets({
  category,
  presets,
  search,
}: {
  category: string | null;
  presets: RetrievalSearchPreset[];
  search: string;
}) {
  return presets.filter((preset) => {
    if (category && preset.category !== category) return false;
    return presetMatchesSearch(preset, search);
  });
}

export function presetMatchesSearch(
  preset: RetrievalSearchPreset,
  search: string,
) {
  const normalizedSearch = search.trim().toLowerCase();
  if (!normalizedSearch) return true;

  return [
    preset.label,
    preset.description,
    preset.query,
    preset.category,
    preset.schema_id,
    preset.detected_format,
    preset.resource_type,
    preset.clinical_domain,
    preset.standard_system,
    preset.source_type,
    ...preset.fields,
    ...preset.target_sources,
    ...preset.launch_hint_targets,
  ].some((value) => value?.toLowerCase().includes(normalizedSearch));
}

export function uniquePresetCategories(presets: RetrievalSearchPreset[]) {
  return Array.from(
    new Set(presets.map((preset) => preset.category).filter(isPresentString)),
  ).sort();
}

function isPresentString(value: string | null | undefined): value is string {
  return Boolean(value);
}
