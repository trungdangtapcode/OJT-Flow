import { humanize } from "../../../lib/utils";
import {
  numberValue,
  optionalStringValue,
  recordValue,
  stringArrayValue,
  stringValue,
} from "./quality-signal-metadata-values";

export function conceptMetadataValues(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((concept) => {
      const standard = stringValue(concept.standard_system, "standard");
      const code = optionalStringValue(concept.code);
      const name = stringValue(concept.display_name, stringValue(concept.concept_id, "concept"));
      const confidence = numberValue(concept.confidence);
      const confidenceText = confidence === null ? "" : ` / ${Math.round(confidence * 100)}%`;
      return `${standard}${code ? ` ${code}` : ""}: ${name}${confidenceText}`;
    })
    .filter(Boolean);
}

export function provenanceIssueMetadataValues(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((issue) => {
      const sourceId = stringValue(issue.source_id, "source");
      const missing = stringArrayValue(issue.missing).map(humanize);
      return `${sourceId}: missing ${missing.length ? missing.join(", ") : "metadata"}`;
    })
    .filter(Boolean);
}

export function suggestedFilterMetadataValues(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .flatMap((filter) =>
      Object.entries(filter)
        .map(([field, rawValue]) => {
          const value = stringValue(rawValue, "");
          return value ? `${humanize(field)}=${value}` : "";
        })
        .filter(Boolean),
    );
}
