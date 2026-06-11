import * as React from "react";

import type { RetrievalPackage } from "../../../types";
import { retrievalTracePanelView } from "../model/retrieval-trace-view-model";

export function useRetrievalWorkspaceView(
  packageData: RetrievalPackage | undefined,
) {
  const tracePanelView = React.useMemo(
    () => retrievalTracePanelView(packageData),
    [packageData],
  );

  return { tracePanelView };
}
