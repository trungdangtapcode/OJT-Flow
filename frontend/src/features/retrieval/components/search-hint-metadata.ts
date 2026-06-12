import {
  optionalStringValue,
  searchHintLineageFollowup,
  searchHintParameterExamples,
  stringArrayValue,
} from "./search-hint-metadata-values";

export type SearchHintParameterExample = {
  example: string;
  matchedDatasetField: boolean;
  name: string;
  targetField: string;
};

export type SearchHintLineageFollowup = {
  parameter: string;
  purpose: string;
};

export type SearchHintMetadataView = {
  capabilityWarning: string | null;
  lineageFollowup: SearchHintLineageFollowup[];
  parameterExamples: SearchHintParameterExample[];
  scopeEndpoints: string[];
  selectedCandidateTitle: string;
  selectedCandidates: string[];
};

export function searchHintMetadataView(
  metadata: Record<string, unknown>,
): SearchHintMetadataView {
  const selectedTerms = stringArrayValue(metadata.selected_terms);
  const selectedUnitCandidates = stringArrayValue(metadata.selected_unit_candidates);
  return {
    capabilityWarning: optionalStringValue(metadata.capability_warning),
    lineageFollowup: searchHintLineageFollowup(metadata.lineage_followup),
    parameterExamples: searchHintParameterExamples(metadata.parameter_examples),
    scopeEndpoints: stringArrayValue(metadata.scope_endpoints),
    selectedCandidateTitle: selectedTerms.length
      ? "Selected terminology terms"
      : "Selected unit candidates",
    selectedCandidates: selectedTerms.length ? selectedTerms : selectedUnitCandidates,
  };
}

export function hasSearchHintMetadataDetails(view: SearchHintMetadataView) {
  return Boolean(
    view.parameterExamples.length ||
      view.lineageFollowup.length ||
      view.scopeEndpoints.length ||
      view.selectedCandidates.length ||
      view.capabilityWarning,
  );
}
