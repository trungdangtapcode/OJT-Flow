import type { RetrievalSearchPayload } from "../../../types";

export type ExecuteRetrievalSearch = (
  overrides?: Partial<RetrievalSearchPayload>,
) => Promise<void>;

export function executeSearchWhen({
  condition,
  executeSearch,
  overrides,
}: {
  condition: boolean;
  executeSearch: ExecuteRetrievalSearch;
  overrides: Partial<RetrievalSearchPayload>;
}) {
  if (condition) void executeSearch(overrides);
}

export function sourceScopeOverride(sourceId: string | null): Partial<RetrievalSearchPayload> {
  return { filters: { source_id: sourceId } };
}
