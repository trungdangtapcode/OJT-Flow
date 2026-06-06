import type { Evidence } from "../../../types";
import type { EvidenceProvenanceEntry } from "./retrieval-evidence-types";
import { optionalStringValue } from "./retrieval-evidence-utils";

export function provenanceEntriesFromEvidence(
  evidence: Evidence,
): EvidenceProvenanceEntry[] {
  const locator = evidence.locator;
  const entries: EvidenceProvenanceEntry[] = [];
  const sourceVersion = optionalStringValue(evidence.source_version);
  if (sourceVersion) entries.push({ href: null, label: "Version", value: sourceVersion });
  const locatorFields: Array<[string, string]> = [
    ["Standard", "standard"],
    ["System", "standard_system"],
    ["URL", "url"],
    ["Path", "path"],
    ["API", "api"],
    ["PMID", "pmid"],
    ["DOI", "doi"],
    ["Resource", "resource"],
    ["Table", "table"],
    ["Document", "document_id"],
    ["Chunk", "chunk_id"],
  ];
  for (const [label, key] of locatorFields) {
    const value = locatorSummaryValue(locator[key]);
    if (value) {
      entries.push({ href: provenanceHrefForLocator(key, value), label, value });
    }
  }
  return uniqueProvenanceEntries(entries).slice(0, 8);
}

export function provenanceHrefForLocator(key: string, value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  if ((key === "url" || key === "api") && /^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }
  if (key === "doi") return `https://doi.org/${encodeURIComponent(trimmed)}`;
  if (key === "pmid" && /^[0-9]+$/.test(trimmed)) {
    return `https://pubmed.ncbi.nlm.nih.gov/${trimmed}/`;
  }
  return null;
}

function locatorSummaryValue(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) return value.trim();
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  if (Array.isArray(value)) {
    const items = value
      .map(locatorSummaryValue)
      .filter((item): item is string => Boolean(item));
    return items.length ? items.slice(0, 3).join(", ") : null;
  }
  return null;
}

function uniqueProvenanceEntries(
  entries: EvidenceProvenanceEntry[],
): EvidenceProvenanceEntry[] {
  const seen = new Set<string>();
  return entries.filter((entry) => {
    const key = `${entry.label}:${entry.value}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
