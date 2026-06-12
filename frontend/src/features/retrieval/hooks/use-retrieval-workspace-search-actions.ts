import { isSupportedFilterField } from "../model/retrieval-filter-model";
import type {
  UseRetrievalSearchActionsArgs,
} from "./retrieval-search-action-types";
import { useRetrievalSearchActions } from "./use-retrieval-search-actions";

type UseRetrievalWorkspaceSearchActionsArgs = Omit<
  UseRetrievalSearchActionsArgs,
  "isSupportedFilterField"
>;

export function useRetrievalWorkspaceSearchActions(
  args: UseRetrievalWorkspaceSearchActionsArgs,
) {
  return useRetrievalSearchActions({
    ...args,
    isSupportedFilterField,
  });
}
