import type { RetrievalSource } from "../../../types";
import type { SourceInventoryReadiness } from "./retrieval-source-inventory-types";
import { uniqueSourceInventoryValues } from "./retrieval-source-inventory-values";

export function sourceInventoryReadiness(
  sources: RetrievalSource[],
  filteredSources: RetrievalSource[],
): SourceInventoryReadiness {
  const chunkCount = filteredSources.reduce((count, source) => count + source.chunk_count, 0);
  const emptySourceCount = filteredSources.filter((source) => source.chunk_count <= 0).length;
  const readiness =
    !sources.length || !filteredSources.length || chunkCount <= 0
      ? "blocked"
      : emptySourceCount > 0 || filteredSources.length < sources.length
        ? "review"
        : "ready";
  return {
    chunkCount,
    domainCount: uniqueSourceInventoryValues(
      filteredSources.map((source) => source.clinical_domain),
    ).length,
    emptySourceCount,
    filteredCount: filteredSources.length,
    readiness,
    sourceCount: sources.length,
    sourceTypeCount: uniqueSourceInventoryValues(
      filteredSources.map((source) => source.source_type),
    ).length,
    standardCount: uniqueSourceInventoryValues(
      filteredSources.map((source) => source.standard_system),
    ).length,
  };
}

export function sourceInventoryReadinessVariant(
  readiness: SourceInventoryReadiness["readiness"],
): "success" | "warning" | "destructive" {
  if (readiness === "ready") return "success";
  if (readiness === "review") return "warning";
  return "destructive";
}

export function sourceInventoryReadinessMessage(
  readiness: SourceInventoryReadiness,
  hasSourceFilters: boolean,
): string {
  if (!readiness.sourceCount) {
    return "No trusted sources are loaded. Reindex the corpus before judging retrieval quality.";
  }
  if (!readiness.filteredCount) {
    return "No trusted sources match the current inventory filters. Clear filters before concluding the corpus lacks coverage.";
  }
  if (!readiness.chunkCount) {
    return "Matching sources have no indexed chunks. Refresh or reindex before relying on retrieval results.";
  }
  if (hasSourceFilters) {
    return "Inventory is filtered. Use this view to inspect available source types, but clear filters for corpus-wide coverage checks.";
  }
  if (readiness.emptySourceCount) {
    return "Some trusted sources have no indexed chunks. Review index integrity before using exact source scope.";
  }
  return "Trusted source inventory is searchable. Use exact source scope only for audit or source-specific debugging.";
}
