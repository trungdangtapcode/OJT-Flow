import type { RetrievalSearchCockpitView } from "../model/retrieval-cockpit-view-model";

export function cockpitCountLabel(
  count: number,
  singular: string,
  plural = `${singular}s`,
) {
  return `${count} ${count === 1 ? singular : plural}`;
}

export function cockpitSourceCoverage(
  diversity: RetrievalSearchCockpitView["diversity"],
): string {
  if (!diversity.enabled) return "off";
  return `${diversity.selectedSourceCount}/${diversity.candidateSourceCount}`;
}
