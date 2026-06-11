import * as React from "react";

import {
  useRetrievalIntegrityQuery,
  useRetrievalReindexMutation,
  workflowErrorMessage,
} from "../../../lib/server-state";
import { formatCount } from "../model/retrieval-format";

export function useRetrievalIntegritySession() {
  const [includeCorpusIntegrity, setIncludeCorpusIntegrity] = React.useState(false);
  const integrityQuery = useRetrievalIntegrityQuery({
    include_seeded: true,
    include_corpus: includeCorpusIntegrity,
  });
  const reindexMutation = useRetrievalReindexMutation();

  const reindex = () => {
    reindexMutation.mutate({ include_seeded: true, include_corpus: true });
  };

  return {
    includeCorpusIntegrity,
    integrityError: integrityQuery.isError
      ? workflowErrorMessage(integrityQuery.error)
      : null,
    integrityQuery,
    reindex,
    reindexError: reindexMutation.isError
      ? workflowErrorMessage(reindexMutation.error)
      : null,
    reindexIsPending: reindexMutation.isPending,
    reindexNotice: reindexMutation.data
      ? `${formatCount(reindexMutation.data.chunks_indexed, "chunk")} indexed with ${String(
          reindexMutation.data.embedding?.provider ?? "configured",
        )} embeddings.`
      : null,
    toggleCorpusIntegrity: () =>
      setIncludeCorpusIntegrity((current) => !current),
  };
}
