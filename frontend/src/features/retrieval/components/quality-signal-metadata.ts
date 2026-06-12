import { humanize } from "../../../lib/utils";
import type { RetrievalQualitySignal } from "../../../types";
import type { QualitySignalMetadataDetail } from "./quality-signal-types";
import {
  conceptMetadataValues,
  provenanceIssueMetadataValues,
  suggestedFilterMetadataValues,
} from "./quality-signal-metadata-sections";
import {
  recordValue,
  stringArrayValue,
} from "./quality-signal-metadata-values";

export function qualitySignalMetadataDetails(
  signal: RetrievalQualitySignal,
): QualitySignalMetadataDetail[] {
  const metadata = recordValue(signal.metadata);
  const details: QualitySignalMetadataDetail[] = [];
  const missingConcepts = conceptMetadataValues(metadata.missing_concepts);
  if (missingConcepts.length) {
    details.push({
      label: "Missing concepts",
      values: missingConcepts,
      variant: "warning",
    });
  }
  const provenanceIssues = provenanceIssueMetadataValues(metadata.issues);
  if (provenanceIssues.length) {
    details.push({
      label: "Provenance issues",
      values: provenanceIssues,
      variant: "warning",
    });
  }
  const missingStandards = stringArrayValue(metadata.missing_standards);
  if (missingStandards.length) {
    details.push({
      label: "Missing standards",
      values: missingStandards,
      variant: "warning",
    });
  }
  const missingAspects = stringArrayValue(metadata.missing_aspects).map(humanize);
  if (missingAspects.length) {
    details.push({
      label: "Missing aspects",
      values: missingAspects,
      variant: "warning",
    });
  }
  const suggestedFilters = suggestedFilterMetadataValues(metadata.suggested_filters);
  if (suggestedFilters.length) {
    details.push({
      label: "Suggested filters",
      values: suggestedFilters,
      variant: "muted",
    });
  }
  return details;
}
