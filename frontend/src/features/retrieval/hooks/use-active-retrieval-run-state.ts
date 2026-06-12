import * as React from "react";

import {
  activeRetrievalRunState,
} from "./retrieval-run-session-history";
import type { UseRetrievalRunSessionArgs } from "./use-retrieval-run-session-types";
import type { useRetrievalRunSessionState } from "./use-retrieval-run-session-state";

type RetrievalRunSessionState = ReturnType<typeof useRetrievalRunSessionState>;

export function useActiveRetrievalRunState({
  activeRunId,
  latestPackageData,
  searchRuns,
}: Pick<RetrievalRunSessionState, "activeRunId" | "searchRuns"> &
  Pick<UseRetrievalRunSessionArgs, "latestPackageData">) {
  return React.useMemo(
    () =>
      activeRetrievalRunState({
        activeRunId,
        latestPackageData,
        searchRuns,
      }),
    [activeRunId, latestPackageData, searchRuns],
  );
}
