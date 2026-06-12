import type { RetrievalSearchPayload, RetrievalSearchTask } from "../../../types";
import {
  plannedTaskSearchOverrides,
} from "../model/retrieval-planned-task-payload";
import type { RetrievalSearchTaskControlSetters } from "./retrieval-search-action-types";
import { applyPlannedTaskControls } from "./retrieval-search-task-controls";

type UseRetrievalPlannedTaskActionArgs = RetrievalSearchTaskControlSetters & {
  executeSearch: (overrides?: Partial<RetrievalSearchPayload>) => Promise<void>;
  markCustomSearch: () => void;
};

export function useRetrievalPlannedTaskAction({
  executeSearch,
  markCustomSearch,
  setClinicalDomain,
  setQuery,
  setSourceId,
  setSourceType,
  setStandardSystem,
  setTrustLevel,
}: UseRetrievalPlannedTaskActionArgs) {
  return (task: RetrievalSearchTask) => {
    markCustomSearch();
    const overrides = plannedTaskSearchOverrides(task);
    applyPlannedTaskControls({
      overrides,
      setters: {
        setClinicalDomain,
        setQuery,
        setSourceId,
        setSourceType,
        setStandardSystem,
        setTrustLevel,
      },
      task,
    });
    void executeSearch(overrides);
  };
}
