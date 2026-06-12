import * as React from "react";

type UseRetrievalWorkspaceClearActionsArgs = {
  clearRelevanceJudgments: () => void;
  clearSearchRunSession: () => void;
};

export function useRetrievalWorkspaceClearActions({
  clearRelevanceJudgments,
  clearSearchRunSession,
}: UseRetrievalWorkspaceClearActionsArgs) {
  const clearSearchRuns = React.useCallback(() => {
    clearSearchRunSession();
    clearRelevanceJudgments();
  }, [clearRelevanceJudgments, clearSearchRunSession]);

  return { clearSearchRuns };
}
