import type { RetrievalSearchPayload, RetrievalSearchTask } from "../../../types";
import type { RetrievalSearchTaskControlSetters } from "./retrieval-search-action-types";

export function applyPlannedTaskControls({
  overrides,
  setters,
  task,
}: {
  overrides: Partial<RetrievalSearchPayload>;
  setters: RetrievalSearchTaskControlSetters;
  task: RetrievalSearchTask;
}) {
  setters.setQuery(task.query);
  if (overrides.clinical_domain !== undefined) {
    setters.setClinicalDomain(overrides.clinical_domain ?? "");
  }
  if (overrides.standard_system !== undefined) {
    setters.setStandardSystem(overrides.standard_system ?? "");
  }
  if (overrides.source_type !== undefined) {
    setters.setSourceType(overrides.source_type ?? "");
  }
  if (overrides.trust_level !== undefined) {
    setters.setTrustLevel(overrides.trust_level ?? "");
  }
  if (overrides.filters?.source_id !== undefined) {
    setters.setSourceId(overrides.filters.source_id ?? "");
  }
}
