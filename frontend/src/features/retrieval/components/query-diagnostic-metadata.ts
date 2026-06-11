export function queryDiagnosticMetadataChips(metadata: Record<string, unknown>): string[] {
  const activeFilters = stringArrayValue(metadata.active_metadata_filters);
  const suggestedStandards = stringArrayValue(metadata.suggested_standards);
  const appliedStandard = optionalStringValue(metadata.applied_standard);
  const tokenCount = numberValue(metadata.query_token_count);
  const filterCount = numberValue(metadata.active_metadata_filter_count);
  return [
    tokenCount !== null ? `${tokenCount} query token${tokenCount === 1 ? "" : "s"}` : "",
    filterCount !== null ? `${filterCount} active filter${filterCount === 1 ? "" : "s"}` : "",
    appliedStandard ? `applied ${appliedStandard}` : "",
    suggestedStandards.length ? `suggested ${suggestedStandards.join(", ")}` : "",
    activeFilters.length ? `filters ${activeFilters.join(", ")}` : "",
  ].filter(Boolean);
}

function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
