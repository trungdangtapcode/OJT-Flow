import * as React from "react";

import type { RetrievalSearchPayload } from "../../../types";
import type { SearchMutationState } from "./use-retrieval-page-workspace-types";

type UseRetrievalWorkspaceSearchSubmitArgs = {
  searchMutation: SearchMutationState;
  setFormError: (message: string | null) => void;
  setPlanControlNotice: (message: string | null) => void;
};

export function useRetrievalWorkspaceSearchSubmit({
  searchMutation,
  setFormError,
  setPlanControlNotice,
}: UseRetrievalWorkspaceSearchSubmitArgs) {
  return React.useCallback(
    async (payload: RetrievalSearchPayload) => {
      setFormError(null);
      setPlanControlNotice(null);
      return searchMutation.mutateAsync(payload);
    },
    [searchMutation, setFormError, setPlanControlNotice],
  );
}
