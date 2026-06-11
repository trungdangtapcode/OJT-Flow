import { humanize } from "../../../lib/utils";
import type {
  RetrievalSearchOption,
  RetrievalSearchOptions,
  RetrievalSearchPreset,
  RetrievalSource,
} from "../../../types";
import { uniqueValues } from "./retrieval-evidence-utils";
import type { RetrievalFormState } from "./retrieval-search-payload";

export type RetrievalQueryBuilderOptionsView = {
  domainOptions: string[];
  formatOptions: RetrievalSearchOption[];
  selectedSource: RetrievalSource | null;
  sourceTypeOptions: string[];
  standardOptions: string[];
  topKOptions: number[];
  trustOptions: string[];
};

export function retrievalQueryBuilderOptionsView({
  formState,
  presets,
  searchOptions,
  sources,
}: {
  formState: RetrievalFormState;
  presets: RetrievalSearchPreset[];
  searchOptions: RetrievalSearchOptions | undefined;
  sources: RetrievalSource[];
}): RetrievalQueryBuilderOptionsView {
  const domains = uniqueValues(sources.map((source) => source.clinical_domain));
  const standards = uniqueValues(sources.map((source) => source.standard_system));
  return {
    domainOptions: uniqueValues([...domains, formState.clinicalDomain]),
    formatOptions: mergeSearchOptions(
      searchOptions?.detected_formats ?? [],
      presets.map((preset) => preset.detected_format),
      formState.detectedFormat,
    ),
    selectedSource: formState.sourceId
      ? sources.find((source) => source.source_id === formState.sourceId) ?? null
      : null,
    sourceTypeOptions: uniqueValues([
      ...sources.map((source) => source.source_type),
      ...presets.map((preset) => preset.source_type),
      formState.sourceType,
    ]),
    standardOptions: uniqueValues([...standards, formState.standardSystem]),
    topKOptions: uniqueNumberValues([
      ...(searchOptions?.top_k_values ?? []),
      formState.topK,
      ...presets.map((preset) => preset.top_k),
    ]),
    trustOptions: uniqueValues([
      ...sources.map((source) => source.trust_level),
      ...presets.map((preset) => preset.trust_level),
      formState.trustLevel,
    ]),
  };
}

export function mergeSearchOptions(
  options: RetrievalSearchOption[],
  additionalValues: Array<string | null | undefined>,
  currentValue: string,
): RetrievalSearchOption[] {
  const merged = new Map<string, RetrievalSearchOption>();
  for (const option of options) {
    if (!option.value) continue;
    merged.set(option.value, option);
  }
  for (const value of [...additionalValues, currentValue]) {
    if (!value || merged.has(value)) continue;
    merged.set(value, { value, label: humanize(value) });
  }
  return Array.from(merged.values()).sort((left, right) =>
    left.label.localeCompare(right.label),
  );
}

export function uniqueNumberValues(values: Array<number | null | undefined>): number[] {
  return Array.from(
    new Set(values.filter((value): value is number => typeof value === "number" && value > 0)),
  ).sort((left, right) => left - right);
}
