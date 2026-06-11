import type {
  useRetrievalGraphContextsQuery,
  useRetrievalGraphNeighborhoodQuery,
  useRetrievalPresetsQuery,
  useRetrievalSearchOptionsQuery,
  useRetrievalSearchMutation,
  useRetrievalSourcesQuery,
  useRuntimeConfigQuery,
  useSchemasQuery,
} from "../../../lib/server-state";
import type { RetrievalGraphNeighborhoodQuery } from "../../../types";
import type { useRetrievalIntegritySession } from "../hooks/use-retrieval-integrity-session";
import type { useRetrievalPageWorkspace } from "../hooks/use-retrieval-page-workspace";

export type RetrievalPagePropsArgs = {
  graphContextsQuery: ReturnType<typeof useRetrievalGraphContextsQuery>;
  graphNeighborhoodQuery: RetrievalGraphNeighborhoodQuery | null;
  graphNeighborhoodResultQuery: ReturnType<typeof useRetrievalGraphNeighborhoodQuery>;
  integritySession: ReturnType<typeof useRetrievalIntegritySession>;
  presetsQuery: ReturnType<typeof useRetrievalPresetsQuery>;
  runtimeQuery: ReturnType<typeof useRuntimeConfigQuery>;
  schemasQuery: ReturnType<typeof useSchemasQuery>;
  searchMutation: ReturnType<typeof useRetrievalSearchMutation>;
  searchOptionsQuery: ReturnType<typeof useRetrievalSearchOptionsQuery>;
  setGraphNeighborhoodQuery: (query: RetrievalGraphNeighborhoodQuery | null) => void;
  sourcesQuery: ReturnType<typeof useRetrievalSourcesQuery>;
  workspace: ReturnType<typeof useRetrievalPageWorkspace>;
};
