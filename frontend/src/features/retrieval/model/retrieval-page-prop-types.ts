import type {
  useRetrievalActiveLearningCandidatesQuery,
  useRetrievalActiveLearningSummaryQuery,
  useRetrievalCorpusPartitionsQuery,
  useRetrievalGraphContextsQuery,
  useRetrievalGraphNeighborhoodQuery,
  useRetrievalFreshnessQuery,
  useRetrievalJudgmentSummaryQuery,
  useRetrievalJudgmentsQuery,
  useRetrievalPresetsQuery,
  useRetrievalSearchOptionsQuery,
  useRetrievalSearchMutation,
  useRetrievalSourcesQuery,
  useRuntimeConfigQuery,
  useSchemasQuery,
  useUpdateRetrievalActiveLearningCandidateMutation,
} from "../../../lib/server-state";
import type { RetrievalGraphNeighborhoodQuery } from "../../../types";
import type { useRetrievalIntegritySession } from "../hooks/use-retrieval-integrity-session";
import type { useRetrievalPageWorkspace } from "../hooks/use-retrieval-page-workspace";

export type RetrievalPagePropsArgs = {
  activeLearningCandidatesQuery: ReturnType<typeof useRetrievalActiveLearningCandidatesQuery>;
  activeLearningSummaryQuery: ReturnType<typeof useRetrievalActiveLearningSummaryQuery>;
  corpusPartitionsQuery: ReturnType<typeof useRetrievalCorpusPartitionsQuery>;
  graphContextsQuery: ReturnType<typeof useRetrievalGraphContextsQuery>;
  graphNeighborhoodQuery: RetrievalGraphNeighborhoodQuery | null;
  graphNeighborhoodResultQuery: ReturnType<typeof useRetrievalGraphNeighborhoodQuery>;
  freshnessQuery: ReturnType<typeof useRetrievalFreshnessQuery>;
  integritySession: ReturnType<typeof useRetrievalIntegritySession>;
  presetsQuery: ReturnType<typeof useRetrievalPresetsQuery>;
  regressionJudgmentsQuery: ReturnType<typeof useRetrievalJudgmentsQuery>;
  regressionSummaryQuery: ReturnType<typeof useRetrievalJudgmentSummaryQuery>;
  runtimeQuery: ReturnType<typeof useRuntimeConfigQuery>;
  schemasQuery: ReturnType<typeof useSchemasQuery>;
  searchMutation: ReturnType<typeof useRetrievalSearchMutation>;
  searchOptionsQuery: ReturnType<typeof useRetrievalSearchOptionsQuery>;
  setGraphNeighborhoodQuery: (query: RetrievalGraphNeighborhoodQuery | null) => void;
  sourcesQuery: ReturnType<typeof useRetrievalSourcesQuery>;
  updateActiveLearningCandidateMutation: ReturnType<
    typeof useUpdateRetrievalActiveLearningCandidateMutation
  >;
  workspace: ReturnType<typeof useRetrievalPageWorkspace>;
};
