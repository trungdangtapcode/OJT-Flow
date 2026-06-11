import * as React from "react";

import {
  useRetrievalGraphContextsQuery,
  useRetrievalGraphNeighborhoodQuery,
  useRetrievalJudgmentSummaryQuery,
  useRetrievalJudgmentsQuery,
  useRetrievalPresetsQuery,
  useRetrievalSearchOptionsQuery,
  useRetrievalSearchMutation,
  useRetrievalSourcesQuery,
  useRuntimeConfigQuery,
  useSchemasQuery,
} from "../../../lib/server-state";
import type { RetrievalGraphNeighborhoodQuery } from "../../../types";
import type { RetrievalPageChrome } from "../components/retrieval-page-chrome";
import type { RetrievalQueryColumn } from "../components/retrieval-query-column";
import type { RetrievalResultsColumn } from "../components/retrieval-results-column";
import { useRetrievalIntegritySession } from "./use-retrieval-integrity-session";
import { useRetrievalPageWorkspace } from "./use-retrieval-page-workspace";
import { retrievalPageProps } from "../model/retrieval-page-props";

export function useRetrievalPageController(): {
  chrome: React.ComponentProps<typeof RetrievalPageChrome>;
  queryColumn: React.ComponentProps<typeof RetrievalQueryColumn>;
  resultsColumn: React.ComponentProps<typeof RetrievalResultsColumn>;
} {
  const presetsQuery = useRetrievalPresetsQuery();
  const searchOptionsQuery = useRetrievalSearchOptionsQuery();
  const sourcesQuery = useRetrievalSourcesQuery();
  const schemasQuery = useSchemasQuery();
  const runtimeQuery = useRuntimeConfigQuery();
  const searchMutation = useRetrievalSearchMutation();
  const integritySession = useRetrievalIntegritySession();
  const presets = presetsQuery.data ?? [];
  const workspace = useRetrievalPageWorkspace({ presets, searchMutation });
  const [graphNeighborhoodQuery, setGraphNeighborhoodQuery] =
    React.useState<RetrievalGraphNeighborhoodQuery | null>(null);
  const graphContextsQuery = useRetrievalGraphContextsQuery({ limit: 20 });
  const graphNeighborhoodResultQuery =
    useRetrievalGraphNeighborhoodQuery(graphNeighborhoodQuery);
  const regressionJudgmentsQuery = useRetrievalJudgmentsQuery(
    { limit: 1000 },
    { enabled: true },
  );
  const regressionSummaryQuery = useRetrievalJudgmentSummaryQuery(
    { limit: 1000 },
    { enabled: true },
  );

  return retrievalPageProps({
    graphContextsQuery,
    graphNeighborhoodQuery,
    graphNeighborhoodResultQuery,
    integritySession,
    presetsQuery,
    regressionJudgmentsQuery,
    regressionSummaryQuery,
    runtimeQuery,
    schemasQuery,
    searchMutation,
    searchOptionsQuery,
    setGraphNeighborhoodQuery,
    sourcesQuery,
    workspace,
  });
}
