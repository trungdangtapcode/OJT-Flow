import type {
  useRetrievalPresetsQuery,
  useRetrievalSearchOptionsQuery,
  useRetrievalSearchMutation,
  useRetrievalSourcesQuery,
  useRuntimeConfigQuery,
  useSchemasQuery,
} from "../../../lib/server-state";
import type { useRetrievalIntegritySession } from "../hooks/use-retrieval-integrity-session";
import type { useRetrievalPageWorkspace } from "../hooks/use-retrieval-page-workspace";

export type RetrievalPagePropsArgs = {
  integritySession: ReturnType<typeof useRetrievalIntegritySession>;
  presetsQuery: ReturnType<typeof useRetrievalPresetsQuery>;
  runtimeQuery: ReturnType<typeof useRuntimeConfigQuery>;
  schemasQuery: ReturnType<typeof useSchemasQuery>;
  searchMutation: ReturnType<typeof useRetrievalSearchMutation>;
  searchOptionsQuery: ReturnType<typeof useRetrievalSearchOptionsQuery>;
  sourcesQuery: ReturnType<typeof useRetrievalSourcesQuery>;
  workspace: ReturnType<typeof useRetrievalPageWorkspace>;
};
