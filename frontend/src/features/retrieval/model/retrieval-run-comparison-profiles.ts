import type { QueryProfileSummary } from "./retrieval-run-summary";

export function queryProfilesChanged(
  active: QueryProfileSummary | null,
  baseline: QueryProfileSummary | null,
): boolean {
  return (
    active?.profileId !== baseline?.profileId ||
    active?.retrievalMode !== baseline?.retrievalMode ||
    active?.route !== baseline?.route
  );
}
