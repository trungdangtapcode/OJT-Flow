import type { RetrievalSource } from "../../../types";

export function getVisibleSourceOptions(sources: RetrievalSource[], search: string) {
  return sources.filter((source) => sourceMatchesSearch(source, search)).slice(0, 8);
}

export function sourceMatchesSearch(source: RetrievalSource, search: string) {
  const normalized = search.trim().toLowerCase();
  if (!normalized) return true;
  return [
    source.source_id,
    source.title,
    source.source_type,
    source.clinical_domain,
    source.standard_system,
  ].some((value) => value?.toLowerCase().includes(normalized));
}

export function formatSourceCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
