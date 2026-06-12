import type * as React from "react";

import { workflowErrorMessage } from "../../../lib/server-state";
import type { RetrievalPageChrome } from "../components/retrieval-page-chrome";
import { retrievalSummaryStripView } from "./retrieval-summary-model";
import type { RetrievalPagePropsArgs } from "./retrieval-page-prop-types";

export function retrievalPageChromeProps({
  integritySession,
  runtimeQuery,
  sourcesQuery,
  workspace,
}: RetrievalPagePropsArgs): React.ComponentProps<typeof RetrievalPageChrome> {
  const sources = sourcesQuery.data ?? [];
  const { packageData } = workspace.runSession;

  return {
    integrityError: integritySession.integrityError,
    onReindex: integritySession.reindex,
    reindexError: integritySession.reindexError,
    reindexIsPending: integritySession.reindexIsPending,
    reindexNotice: integritySession.reindexNotice,
    sourcesError: sourcesQuery.isError
      ? workflowErrorMessage(sourcesQuery.error)
      : null,
    summary: retrievalSummaryStripView({
      packageData,
      runtime: runtimeQuery.data,
      sources,
      sourcesLoading: sourcesQuery.isLoading,
    }),
  };
}
