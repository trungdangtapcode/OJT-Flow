import type * as React from "react";

import type { RetrievalResultsColumn } from "../components/retrieval-results-column";
import { formatCount } from "./retrieval-format";
import {
  integrityBadgeVariant,
  prioritizedIntegrityChecks,
  shortHash,
} from "./retrieval-integrity-model";
import type { RetrievalPagePropsArgs } from "./retrieval-page-prop-types";
import { retrievalPageSearchResultsProps } from "./retrieval-page-search-results-props";
import { retrievalPageTraceProps } from "./retrieval-page-trace-props";
import { retrievalRuntimeStatusStripView } from "./retrieval-summary-model";

export function retrievalPageResultsColumnProps({
  integritySession,
  searchMutation,
  sourcesQuery,
  workspace,
}: RetrievalPagePropsArgs): React.ComponentProps<typeof RetrievalResultsColumn> {
  const sources = sourcesQuery.data ?? [];
  const { runSession, searchActions } = workspace;
  const { packageData } = runSession;
  const runtimeStatusView = retrievalRuntimeStatusStripView({
    integrityStatus: integritySession.integrityQuery.data?.status ?? "loading",
    packageData,
  });

  return {
    graph: { graphContext: packageData?.handoff_context.graph_context },
    integrity: {
      checks: integritySession.integrityQuery.data
        ? prioritizedIntegrityChecks(integritySession.integrityQuery.data)
        : [],
      formatCount,
      formatHash: shortHash,
      includeCorpus: integritySession.includeCorpusIntegrity,
      integrityBadgeVariant,
      isFetching: integritySession.integrityQuery.isFetching,
      onRefresh: () => void integritySession.integrityQuery.refetch(),
      onToggleCorpus: integritySession.toggleCorpusIntegrity,
      report: integritySession.integrityQuery.data,
    },
    runtimeStatus: runtimeStatusView ? { view: runtimeStatusView } : null,
    searchResults: retrievalPageSearchResultsProps({ searchMutation, workspace }),
    sourceInventory: {
      isLoading: sourcesQuery.isLoading,
      onUseSource: searchActions.applySourceIdFilter,
      sources,
    },
    trace: retrievalPageTraceProps({ searchMutation, workspace }),
  };
}
