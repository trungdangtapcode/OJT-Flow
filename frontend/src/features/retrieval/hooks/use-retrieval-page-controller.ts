import type * as React from "react";

import {
  useRetrievalPresetsQuery,
  useRetrievalSearchOptionsQuery,
  useRetrievalSearchMutation,
  useRetrievalSourcesQuery,
  useRuntimeConfigQuery,
  useSchemasQuery,
} from "../../../lib/server-state";
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

  return retrievalPageProps({
    integritySession,
    presetsQuery,
    runtimeQuery,
    schemasQuery,
    searchMutation,
    searchOptionsQuery,
    sourcesQuery,
    workspace,
  });
}
