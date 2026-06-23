import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  ApiRequestError,
  API_BASE_URL,
  appendAssistantSessionMessage,
  archiveAssistantSession,
  chatWithAssistant,
  createAssistantSession,
  createClipboardImageParseJob,
  createRetrievalReindexJob,
  createWorkflow,
  deleteAssistantSession,
  deleteAssistantMemoryPreference,
  deleteRetrievalJudgment,
  enqueueRetrievalActiveLearningCandidate,
  evaluateRetrievalJudgments,
  extractFileText,
  getAssistantSession,
  getAssistantSessionStreamReplays,
  getAssistantMemory,
  getAssistantMemoryPolicy,
  getAssistantMcpPrompts,
  getAssistantMcpResources,
  getGraphMedStatus,
  getKnowledgeGraphNeighborhood,
  getKnowledgeGraphStats,
  getJob,
  getExtractorInventory,
  getRetrievalJudgmentSummary,
  getRetrievalActiveLearningSummary,
  getRetrievalIntegrity,
  getRetrievalCorpusAdapters,
  getRetrievalCorpusChunkingProfiles,
  getRetrievalCorpusManifest,
  getRetrievalCorpusPartitions,
  getRetrievalGraphNeighborhood,
  getRetrievalSearchOptions,
  getRetrievalSourcePolicies,
  getRetrievalStrategies,
  getRuntimeConfig,
  getRuntimeAiRiskRegister,
  getRuntimeDisclaimers,
  getRetrievalFreshness,
  getRuntimeHealth,
  getRuntimeMigrations,
  getRuntimeOwaspLlmThreatModel,
  getRuntimeReadiness,
  getWorkflow,
  getWorkflowInputPreview,
  getWorkflowOutput,
  getWorkflowStats,
  ingestPrivateCorpus,
  importKnowledgeGraph,
  importKnowledgeGraphFile,
  listAssistantTools,
  listAssistantAnswerTemplates,
  listAssistantExamples,
  listAssistantSessions,
  listJobs,
  listRetrievalGraphContexts,
  listRetrievalActiveLearningCandidates,
  listRetrievalJudgments,
  listRetrievalPresets,
  listRetrievalSources,
  listReviewSummaries,
  listSchemas,
  listWorkflowEvents,
  normalizeOcrEvidence,
  listWorkflowSummaries,
  planRetrieval,
  reindexRetrieval,
  renameAssistantSession,
  searchRetrieval,
  searchKnowledgeGraph,
  streamAssistantChat,
  submitReview,
  updateRuntimeAssistantSettings,
  updateRuntimeRetrievalSettings,
  updateRetrievalActiveLearningCandidate,
  upsertAssistantMemoryPreference,
  upsertRetrievalJudgment,
  uploadFileWorkflow,
} from "../api";
import { apiErrorMessage } from "./api-error-diagnostics";
import type {
  AssistantChatPayload,
  AssistantChatMessage,
  AssistantChatSessionDetail,
  AssistantChatSessionSummary,
  AssistantMemoryPolicy,
  AssistantMemoryPreference,
  AssistantMemoryPreferencePayload,
  AssistantMemorySnapshot,
  AssistantSessionCreatePayload,
  AssistantSessionMessagePayload,
  AssistantSessionRenamePayload,
  AssistantResponse,
  AssistantStreamEvent,
  AssistantStreamReplay,
  BackgroundJob,
  DisclaimerPolicy,
  OcrEvidenceFieldInput,
  OcrEvidenceResponse,
  UploadParseJobResponse,
  RetrievalGraphNeighborhoodQuery,
  KnowledgeGraphImportPayload,
  KnowledgeGraphImportResult,
  PrivateCorpusIngestPayload,
  RetrievalActiveLearningCandidatePayload,
  RetrievalActiveLearningCandidateUpdatePayload,
  RetrievalActiveLearningPriority,
  RetrievalActiveLearningSourceKind,
  RetrievalActiveLearningStatus,
  RetrievalReindexJobPayload,
  RetrievalJudgmentEvaluationPayload,
  RetrievalJudgmentPayload,
  RetrievalPlan,
  RetrievalReindexPayload,
  RetrievalSearchPayload,
  RuntimeAssistantSettingsPayload,
  AiRiskRegister,
  OwaspLlmThreatModel,
  RuntimeRetrievalSettingsPayload,
  StartWorkflowPayload,
} from "../types";

type AssistantStreamMutationPayload = {
  payload: AssistantChatPayload;
  onEvent: (event: AssistantStreamEvent) => void;
  signal?: AbortSignal;
};

type AppendAssistantSessionMessageInput = {
  sessionId: string;
  payload: AssistantSessionMessagePayload;
};

type UpsertAssistantMemoryInput = {
  key: string;
  payload: AssistantMemoryPreferencePayload;
};

type RetrievalReindexJobInput = {
  payload: RetrievalReindexJobPayload;
};

type ClipboardImageParseJobInput = {
  dataBase64: string;
  filename: string;
  mimeType: string;
  extractor: string;
  executeNow: boolean;
};

type PrivateCorpusIngestInput = {
  payload: PrivateCorpusIngestPayload;
};

export const queryKeys = {
  stats: ["workflow-stats"] as const,
  workflowSummaries: (params: Record<string, unknown>) => ["workflow-summaries", params] as const,
  reviewSummaries: (params: Record<string, unknown>) => ["review-summaries", params] as const,
  workflow: (workflowId: string | null) => ["workflow", workflowId] as const,
  inputPreview: (workflowId: string | null) => ["workflow-input-preview", workflowId] as const,
  output: (workflowId: string | null) => ["workflow-output", workflowId] as const,
  events: (workflowId: string | null) => ["workflow-events", workflowId] as const,
  schemas: ["schemas"] as const,
  retrievalSources: ["retrieval-sources"] as const,
  retrievalJudgments: (params: Record<string, unknown>) =>
    ["retrieval-judgments", params] as const,
  retrievalJudgmentSummary: (params: Record<string, unknown>) =>
    ["retrieval-judgment-summary", params] as const,
  retrievalJudgmentEvaluation: (params: Record<string, unknown>) =>
    ["retrieval-judgment-evaluation", params] as const,
  retrievalActiveLearningCandidates: (params: Record<string, unknown>) =>
    ["retrieval-active-learning-candidates", params] as const,
  retrievalActiveLearningSummary: (params: Record<string, unknown>) =>
    ["retrieval-active-learning-summary", params] as const,
  retrievalSearchOptions: ["retrieval-search-options"] as const,
  retrievalCorpusAdapters: ["retrieval-corpus-adapters"] as const,
  retrievalCorpusChunkingProfiles: ["retrieval-corpus-chunking-profiles"] as const,
  retrievalCorpusManifest: ["retrieval-corpus-manifest"] as const,
  retrievalCorpusPartitions: ["retrieval-corpus-partitions"] as const,
  retrievalSourcePolicies: ["retrieval-source-policies"] as const,
  retrievalStrategies: ["retrieval-strategies"] as const,
  retrievalGraphContexts: (params: Record<string, unknown>) =>
    ["retrieval-graph-contexts", params] as const,
  retrievalGraphNeighborhood: (params: RetrievalGraphNeighborhoodQuery | null) =>
    ["retrieval-graph-neighborhood", params] as const,
  knowledgeGraphStats: ["knowledge-graph-stats"] as const,
  graphMedStatus: ["graph-med-status"] as const,
  knowledgeGraphSearch: (params: Record<string, unknown>) =>
    ["knowledge-graph-search", params] as const,
  knowledgeGraphNeighborhood: (params: Record<string, unknown> | null) =>
    ["knowledge-graph-neighborhood", params] as const,
  retrievalPlan: (payload: RetrievalSearchPayload | null) => ["retrieval-plan", payload] as const,
  retrievalIntegrity: (params: Record<string, unknown>) => ["retrieval-integrity", params] as const,
  retrievalFreshness: ["retrieval-freshness"] as const,
  extractors: ["extractors"] as const,
  health: ["runtime-health"] as const,
  runtimeConfig: ["runtime-config"] as const,
  runtimeAiRiskRegister: ["runtime-ai-risk-register"] as const,
  runtimeDisclaimers: ["runtime-disclaimers"] as const,
  runtimeOwaspLlmThreatModel: ["runtime-owasp-llm-threat-model"] as const,
  runtimeMigrations: ["runtime-migrations"] as const,
  runtimeReadiness: ["runtime-readiness"] as const,
  jobs: (params: Record<string, unknown>) => ["jobs", params] as const,
  job: (jobId: string | null) => ["job", jobId] as const,
  assistantTools: ["assistant-tools"] as const,
  assistantAnswerTemplates: ["assistant-answer-templates"] as const,
  assistantMcpPrompts: ["assistant-mcp-prompts"] as const,
  assistantMcpResources: ["assistant-mcp-resources"] as const,
  assistantMemoryPolicy: ["assistant-memory-policy"] as const,
  assistantMemory: ["assistant-memory"] as const,
  assistantExamples: ["assistant-examples"] as const,
  assistantSessions: (params: Record<string, unknown>) =>
    ["assistant-sessions", params] as const,
  assistantSession: (sessionId: string | null) => ["assistant-session", sessionId] as const,
  assistantStreamReplays: (sessionId: string | null) =>
    ["assistant-stream-replays", sessionId] as const,
  retrievalPresets: ["retrieval-presets"] as const,
};

export const runtimeConfig = {
  apiBaseUrl: API_BASE_URL,
} as const;

export function useWorkflowStatsQuery() {
  return useQuery({ queryKey: queryKeys.stats, queryFn: getWorkflowStats });
}

export function useWorkflowSummariesQuery(params: {
  status?: string | null;
  q?: string | null;
  page?: number;
  page_size?: number;
  sort?: string;
  direction?: string;
}) {
  return useQuery({
    queryKey: queryKeys.workflowSummaries(params),
    queryFn: () => listWorkflowSummaries(params),
    placeholderData: (previous) => previous,
  });
}

export function useReviewSummariesQuery(params: {
  status?: string | null;
  q?: string | null;
  page?: number;
  page_size?: number;
  sort?: string;
  direction?: string;
}) {
  return useQuery({
    queryKey: queryKeys.reviewSummaries(params),
    queryFn: () => listReviewSummaries(params),
    placeholderData: (previous) => previous,
  });
}

export function useWorkflowQuery(workflowId: string | null) {
  return useQuery({
    enabled: Boolean(workflowId),
    queryKey: queryKeys.workflow(workflowId),
    queryFn: () => getWorkflow(workflowId!),
  });
}

export function useWorkflowEventsQuery(workflowId: string | null) {
  return useQuery({
    enabled: Boolean(workflowId),
    queryKey: queryKeys.events(workflowId),
    queryFn: () => listWorkflowEvents(workflowId!),
  });
}

export function useWorkflowInputPreviewQuery(workflowId: string | null, enabled: boolean) {
  return useQuery({
    enabled: Boolean(workflowId) && enabled,
    queryKey: queryKeys.inputPreview(workflowId),
    queryFn: () => getWorkflowInputPreview(workflowId!),
  });
}

export function useWorkflowOutputQuery(workflowId: string | null, enabled: boolean) {
  return useQuery({
    enabled: Boolean(workflowId) && enabled,
    queryKey: queryKeys.output(workflowId),
    queryFn: () => getWorkflowOutput(workflowId!),
  });
}

export function useExtractorInventoryQuery() {
  return useQuery({ queryKey: queryKeys.extractors, queryFn: getExtractorInventory });
}

export function useExtractFileTextMutation() {
  return useMutation({
    mutationFn: ({ file, extractor }: { file: File; extractor: string }) =>
      extractFileText(file, { extractor }),
  });
}

export function useClipboardImageParseJobMutation() {
  return useMutation<UploadParseJobResponse, Error, ClipboardImageParseJobInput>({
    mutationFn: (payload) =>
      createClipboardImageParseJob({
        data_base64: payload.dataBase64,
        filename: payload.filename,
        mime_type: payload.mimeType,
        extractor: payload.extractor,
        execute_now: payload.executeNow,
        include_extracted_document: true,
      }),
  });
}

export function useRuntimeHealthQuery() {
  return useQuery({ queryKey: queryKeys.health, queryFn: getRuntimeHealth });
}

export function useRuntimeConfigQuery() {
  return useQuery({ queryKey: queryKeys.runtimeConfig, queryFn: getRuntimeConfig });
}

export function useRuntimeAiRiskRegisterQuery() {
  return useQuery<AiRiskRegister>({
    queryKey: queryKeys.runtimeAiRiskRegister,
    queryFn: getRuntimeAiRiskRegister,
  });
}

export function useRuntimeDisclaimersQuery() {
  return useQuery<DisclaimerPolicy>({
    queryKey: queryKeys.runtimeDisclaimers,
    queryFn: getRuntimeDisclaimers,
  });
}

export function useRuntimeOwaspLlmThreatModelQuery() {
  return useQuery<OwaspLlmThreatModel>({
    queryKey: queryKeys.runtimeOwaspLlmThreatModel,
    queryFn: getRuntimeOwaspLlmThreatModel,
  });
}

export function useRuntimeReadinessQuery() {
  return useQuery({ queryKey: queryKeys.runtimeReadiness, queryFn: getRuntimeReadiness });
}

export function useRuntimeMigrationsQuery() {
  return useQuery({ queryKey: queryKeys.runtimeMigrations, queryFn: getRuntimeMigrations });
}

export function useJobsQuery(params: {
  status?: string | null;
  job_type?: string | null;
  limit?: number;
} = {}) {
  return useQuery({
    queryKey: queryKeys.jobs(params),
    queryFn: () => listJobs(params),
  });
}

export function useJobQuery(jobId: string | null) {
  return useQuery<BackgroundJob>({
    enabled: Boolean(jobId),
    queryKey: queryKeys.job(jobId),
    queryFn: () => getJob(jobId!),
  });
}

export function useRetrievalReindexJobMutation() {
  const queryClient = useQueryClient();
  return useMutation<BackgroundJob, Error, RetrievalReindexJobInput>({
    mutationFn: ({ payload }) => createRetrievalReindexJob(payload),
    onSuccess: async (job) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["jobs"] }),
        queryClient.invalidateQueries({ queryKey: queryKeys.job(job.job_id) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.retrievalFreshness }),
      ]);
    },
  });
}

export function useRuntimeRetrievalSettingsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RuntimeRetrievalSettingsPayload) =>
      updateRuntimeRetrievalSettings(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.runtimeConfig }),
        queryClient.invalidateQueries({ queryKey: queryKeys.runtimeReadiness }),
        queryClient.invalidateQueries({ queryKey: queryKeys.retrievalSources }),
        queryClient.invalidateQueries({ queryKey: queryKeys.retrievalSearchOptions }),
        queryClient.invalidateQueries({ queryKey: ["retrieval-integrity"] }),
        queryClient.invalidateQueries({ queryKey: queryKeys.retrievalFreshness }),
      ]);
      toast.success("Retrieval settings reloaded");
    },
  });
}

export function useRuntimeAssistantSettingsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RuntimeAssistantSettingsPayload) =>
      updateRuntimeAssistantSettings(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.runtimeConfig }),
        queryClient.invalidateQueries({ queryKey: queryKeys.runtimeReadiness }),
      ]);
      toast.success("Assistant settings reloaded");
    },
  });
}

export function useSchemasQuery() {
  return useQuery({ queryKey: queryKeys.schemas, queryFn: listSchemas });
}

export function useRetrievalSourcesQuery() {
  return useQuery({ queryKey: queryKeys.retrievalSources, queryFn: listRetrievalSources });
}

export function useRetrievalPresetsQuery() {
  return useQuery({ queryKey: queryKeys.retrievalPresets, queryFn: listRetrievalPresets });
}

export function useRetrievalSearchOptionsQuery() {
  return useQuery({ queryKey: queryKeys.retrievalSearchOptions, queryFn: getRetrievalSearchOptions });
}

export function useRetrievalCorpusAdaptersQuery() {
  return useQuery({
    queryKey: queryKeys.retrievalCorpusAdapters,
    queryFn: getRetrievalCorpusAdapters,
  });
}

export function useRetrievalCorpusPartitionsQuery() {
  return useQuery({
    queryKey: queryKeys.retrievalCorpusPartitions,
    queryFn: getRetrievalCorpusPartitions,
  });
}

export function useRetrievalCorpusManifestQuery() {
  return useQuery({
    queryKey: queryKeys.retrievalCorpusManifest,
    queryFn: getRetrievalCorpusManifest,
  });
}

export function useRetrievalCorpusChunkingProfilesQuery() {
  return useQuery({
    queryKey: queryKeys.retrievalCorpusChunkingProfiles,
    queryFn: getRetrievalCorpusChunkingProfiles,
  });
}

export function useRetrievalSourcePoliciesQuery() {
  return useQuery({
    queryKey: queryKeys.retrievalSourcePolicies,
    queryFn: getRetrievalSourcePolicies,
  });
}

export function useRetrievalStrategiesQuery() {
  return useQuery({
    queryKey: queryKeys.retrievalStrategies,
    queryFn: getRetrievalStrategies,
  });
}

export function useRetrievalGraphContextsQuery(params: {
  workflow_id?: string | null;
  limit?: number;
}) {
  return useQuery({
    queryKey: queryKeys.retrievalGraphContexts(params),
    queryFn: () => listRetrievalGraphContexts(params),
  });
}

export function useRetrievalGraphNeighborhoodQuery(
  params: RetrievalGraphNeighborhoodQuery | null,
) {
  return useQuery({
    enabled: Boolean(params),
    queryKey: queryKeys.retrievalGraphNeighborhood(params),
    queryFn: () => getRetrievalGraphNeighborhood(params!),
  });
}

export function useKnowledgeGraphStatsQuery() {
  return useQuery({
    queryKey: queryKeys.knowledgeGraphStats,
    queryFn: getKnowledgeGraphStats,
  });
}

export function useGraphMedStatusQuery() {
  return useQuery({
    queryKey: queryKeys.graphMedStatus,
    queryFn: getGraphMedStatus,
  });
}

export function useKnowledgeGraphSearchQuery(
  params: { q?: string | null; limit?: number },
  options: { enabled?: boolean } = {},
) {
  return useQuery({
    enabled: options.enabled ?? true,
    queryKey: queryKeys.knowledgeGraphSearch(params),
    queryFn: () => searchKnowledgeGraph(params),
    placeholderData: (previous) => previous,
  });
}

export function useKnowledgeGraphNeighborhoodQuery(
  params: { node_id?: string | null; q?: string | null; depth?: number; limit?: number } | null,
  options: { enabled?: boolean } = {},
) {
  return useQuery({
    enabled: (options.enabled ?? true) && Boolean(params),
    queryKey: queryKeys.knowledgeGraphNeighborhood(params),
    queryFn: () => getKnowledgeGraphNeighborhood(params!),
    placeholderData: (previous) => previous,
  });
}

export function useKnowledgeGraphImportMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: KnowledgeGraphImportPayload) => importKnowledgeGraph(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.knowledgeGraphStats }),
        queryClient.invalidateQueries({ queryKey: ["knowledge-graph-search"] }),
        queryClient.invalidateQueries({ queryKey: ["knowledge-graph-neighborhood"] }),
      ]);
    },
  });
}

export function useKnowledgeGraphFileImportMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      file: File;
      document_id?: string | null;
      source_id?: string | null;
      patient_id?: string | null;
      encounter_id?: string | null;
    }): Promise<KnowledgeGraphImportResult> => importKnowledgeGraphFile(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.knowledgeGraphStats }),
        queryClient.invalidateQueries({ queryKey: queryKeys.graphMedStatus }),
        queryClient.invalidateQueries({ queryKey: ["knowledge-graph-search"] }),
        queryClient.invalidateQueries({ queryKey: ["knowledge-graph-neighborhood"] }),
      ]);
    },
  });
}

export function useRetrievalIntegrityQuery(params: {
  include_seeded: boolean;
  include_corpus: boolean;
}) {
  return useQuery({
    queryKey: queryKeys.retrievalIntegrity(params),
    queryFn: () => getRetrievalIntegrity(params),
  });
}

export function useRetrievalFreshnessQuery() {
  return useQuery({
    queryKey: queryKeys.retrievalFreshness,
    queryFn: getRetrievalFreshness,
  });
}

export function useRetrievalSearchMutation() {
  return useMutation({
    mutationFn: (payload: RetrievalSearchPayload) => searchRetrieval(payload),
  });
}

export function usePrivateCorpusIngestMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ payload }: PrivateCorpusIngestInput) => ingestPrivateCorpus(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.retrievalSources }),
        queryClient.invalidateQueries({ queryKey: queryKeys.retrievalFreshness }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.retrievalIntegrity({
            include_seeded: true,
            include_corpus: true,
          }),
        }),
      ]);
    },
  });
}

export function useRetrievalPlanQuery(payload: RetrievalSearchPayload | null) {
  return useQuery<RetrievalPlan>({
    enabled: Boolean(payload?.query.trim()),
    queryKey: queryKeys.retrievalPlan(payload),
    queryFn: () => planRetrieval(payload!),
  });
}

export function useRetrievalJudgmentsQuery(params: {
  query?: string | null;
  run_id?: string | null;
  evidence_id?: string | null;
  limit?: number;
}, options: { enabled?: boolean } = {}) {
  const enabled =
    options.enabled ?? Boolean(params.query || params.run_id || params.evidence_id);
  return useQuery({
    enabled,
    queryKey: queryKeys.retrievalJudgments(params),
    queryFn: () => listRetrievalJudgments(params),
  });
}

export function useRetrievalJudgmentSummaryQuery(params: {
  query?: string | null;
  limit?: number;
}, options: { enabled?: boolean } = {}) {
  return useQuery({
    enabled: options.enabled ?? Boolean(params.query),
    queryKey: queryKeys.retrievalJudgmentSummary(params),
    queryFn: () => getRetrievalJudgmentSummary(params),
  });
}

export function useRetrievalJudgmentEvaluationQuery(
  payload: RetrievalJudgmentEvaluationPayload | null,
) {
  return useQuery({
    enabled: Boolean(payload && payload.ranked_evidence_ids.length),
    queryKey: queryKeys.retrievalJudgmentEvaluation(payload ?? {}),
    queryFn: () => evaluateRetrievalJudgments(payload!),
  });
}

export function useRetrievalJudgmentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RetrievalJudgmentPayload) => upsertRetrievalJudgment(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["retrieval-judgments"] });
      await queryClient.invalidateQueries({ queryKey: ["retrieval-judgment-summary"] });
      await queryClient.invalidateQueries({ queryKey: ["retrieval-judgment-evaluation"] });
      await queryClient.invalidateQueries({
        queryKey: ["retrieval-active-learning-candidates"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["retrieval-active-learning-summary"],
      });
    },
  });
}

export function useDeleteRetrievalJudgmentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (judgmentId: string) => deleteRetrievalJudgment(judgmentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["retrieval-judgments"] });
      await queryClient.invalidateQueries({ queryKey: ["retrieval-judgment-summary"] });
      await queryClient.invalidateQueries({ queryKey: ["retrieval-judgment-evaluation"] });
    },
  });
}

export function useRetrievalActiveLearningCandidatesQuery(params: {
  status?: RetrievalActiveLearningStatus | null;
  source_kind?: RetrievalActiveLearningSourceKind | null;
  priority?: RetrievalActiveLearningPriority | null;
  query?: string | null;
  limit?: number;
}, options: { enabled?: boolean } = {}) {
  return useQuery({
    enabled: options.enabled ?? true,
    queryKey: queryKeys.retrievalActiveLearningCandidates(params),
    queryFn: () => listRetrievalActiveLearningCandidates(params),
  });
}

export function useRetrievalActiveLearningSummaryQuery(params: { limit?: number } = {}) {
  return useQuery({
    queryKey: queryKeys.retrievalActiveLearningSummary(params),
    queryFn: () => getRetrievalActiveLearningSummary(params),
  });
}

export function useEnqueueRetrievalActiveLearningCandidateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RetrievalActiveLearningCandidatePayload) =>
      enqueueRetrievalActiveLearningCandidate(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["retrieval-active-learning-candidates"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["retrieval-active-learning-summary"],
      });
    },
  });
}

export function useUpdateRetrievalActiveLearningCandidateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      candidateId,
      payload,
    }: {
      candidateId: string;
      payload: RetrievalActiveLearningCandidateUpdatePayload;
    }) => updateRetrievalActiveLearningCandidate(candidateId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["retrieval-active-learning-candidates"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["retrieval-active-learning-summary"],
      });
    },
  });
}

export function useAssistantChatMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AssistantChatPayload) => chatWithAssistant(payload),
    onSuccess: async (response) => {
      if (
        response.tool_calls.some(
          (call) => call.tool_name === "start_workflow" && call.status === "completed",
        )
      ) {
        await invalidateWorkflowCollections(queryClient);
      }
    },
  });
}

export function useAssistantChatStreamMutation() {
  const queryClient = useQueryClient();
  return useMutation<AssistantResponse, Error, AssistantStreamMutationPayload>({
    mutationFn: ({ payload, onEvent, signal }) =>
      streamAssistantChat(payload, onEvent, signal),
    onSuccess: async (response, variables) => {
      if (variables.payload.session_id) {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.assistantStreamReplays(variables.payload.session_id),
        });
      }
      if (
        response.tool_calls.some(
          (call) => call.tool_name === "start_workflow" && call.status === "completed",
        )
      ) {
        await invalidateWorkflowCollections(queryClient);
      }
    },
  });
}

export function useAssistantSessionsQuery(params: {
  include_archived?: boolean;
  limit?: number;
  q?: string;
} = {}) {
  return useQuery({
    queryKey: queryKeys.assistantSessions(params),
    queryFn: () => listAssistantSessions(params),
  });
}

export function useAssistantSessionQuery(sessionId: string | null) {
  return useQuery<AssistantChatSessionDetail>({
    enabled: Boolean(sessionId),
    queryKey: queryKeys.assistantSession(sessionId),
    queryFn: () => getAssistantSession(sessionId!),
  });
}

export function useAssistantStreamReplaysQuery(sessionId: string | null) {
  return useQuery<AssistantStreamReplay[]>({
    enabled: Boolean(sessionId),
    queryKey: queryKeys.assistantStreamReplays(sessionId),
    queryFn: () => getAssistantSessionStreamReplays(sessionId!),
  });
}

export function useCreateAssistantSessionMutation() {
  const queryClient = useQueryClient();
  return useMutation<AssistantChatSessionSummary, Error, AssistantSessionCreatePayload>({
    mutationFn: (payload) => createAssistantSession(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["assistant-sessions"] });
    },
  });
}

export function useRenameAssistantSessionMutation() {
  const queryClient = useQueryClient();
  return useMutation<
    AssistantChatSessionSummary,
    Error,
    { sessionId: string; payload: AssistantSessionRenamePayload }
  >({
    mutationFn: ({ sessionId, payload }) => renameAssistantSession(sessionId, payload),
    onSuccess: async (session) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["assistant-sessions"] }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.assistantSession(session.session_id),
        }),
      ]);
    },
  });
}

export function useArchiveAssistantSessionMutation() {
  const queryClient = useQueryClient();
  return useMutation<AssistantChatSessionSummary, Error, string>({
    mutationFn: (sessionId) => archiveAssistantSession(sessionId),
    onSuccess: async (session) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["assistant-sessions"] }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.assistantSession(session.session_id),
        }),
      ]);
    },
  });
}

export function useDeleteAssistantSessionMutation() {
  const queryClient = useQueryClient();
  return useMutation<{ deleted: boolean; session_id: string }, Error, string>({
    mutationFn: (sessionId) => deleteAssistantSession(sessionId),
    onSuccess: async (result) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["assistant-sessions"] }),
        queryClient.removeQueries({
          queryKey: queryKeys.assistantSession(result.session_id),
        }),
      ]);
    },
  });
}

export function useAppendAssistantSessionMessageMutation() {
  const queryClient = useQueryClient();
  return useMutation<AssistantChatMessage, Error, AppendAssistantSessionMessageInput>({
    mutationFn: ({ sessionId, payload }) =>
      appendAssistantSessionMessage(sessionId, payload),
    onSuccess: async (_, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["assistant-sessions"] }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.assistantSession(variables.sessionId),
        }),
      ]);
    },
  });
}

export function useAssistantToolsQuery() {
  return useQuery({ queryKey: queryKeys.assistantTools, queryFn: listAssistantTools });
}

export function useAssistantAnswerTemplatesQuery() {
  return useQuery({
    queryKey: queryKeys.assistantAnswerTemplates,
    queryFn: listAssistantAnswerTemplates,
  });
}

export function useAssistantMcpResourcesQuery() {
  return useQuery({
    queryKey: queryKeys.assistantMcpResources,
    queryFn: getAssistantMcpResources,
  });
}

export function useAssistantMcpPromptsQuery() {
  return useQuery({
    queryKey: queryKeys.assistantMcpPrompts,
    queryFn: getAssistantMcpPrompts,
  });
}

export function useAssistantMemoryPolicyQuery() {
  return useQuery<AssistantMemoryPolicy>({
    queryKey: queryKeys.assistantMemoryPolicy,
    queryFn: getAssistantMemoryPolicy,
  });
}

export function useAssistantMemoryQuery() {
  return useQuery<AssistantMemorySnapshot>({
    queryKey: queryKeys.assistantMemory,
    queryFn: getAssistantMemory,
  });
}

export function useUpsertAssistantMemoryMutation() {
  const queryClient = useQueryClient();
  return useMutation<AssistantMemoryPreference, Error, UpsertAssistantMemoryInput>({
    mutationFn: ({ key, payload }) => upsertAssistantMemoryPreference(key, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.assistantMemory });
    },
  });
}

export function useDeleteAssistantMemoryMutation() {
  const queryClient = useQueryClient();
  return useMutation<{ deleted: boolean; key: string }, Error, string>({
    mutationFn: (key) => deleteAssistantMemoryPreference(key),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.assistantMemory });
    },
  });
}

export function useOcrEvidenceMutation() {
  return useMutation<OcrEvidenceResponse, Error, OcrEvidenceFieldInput[]>({
    mutationFn: normalizeOcrEvidence,
  });
}

export function useAssistantExamplesQuery() {
  return useQuery({
    queryKey: queryKeys.assistantExamples,
    queryFn: listAssistantExamples,
  });
}

export function useRetrievalReindexMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RetrievalReindexPayload) => reindexRetrieval(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.retrievalSources });
      await queryClient.invalidateQueries({ queryKey: ["retrieval-integrity"] });
      toast.success("Retrieval index refreshed");
    },
  });
}

export function useCreateWorkflowMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: StartWorkflowPayload) => createWorkflow(payload),
    onSuccess: async () => {
      await invalidateWorkflowCollections(queryClient);
      toast.success("Workflow created");
    },
    onError: async (error) => {
      if (workflowErrorWorkflowId(error)) {
        await invalidateWorkflowCollections(queryClient);
      }
    },
  });
}

export function useUploadWorkflowMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UploadWorkflowPayload) =>
      uploadFileWorkflow(payload.file, payload.options),
    onSuccess: async () => {
      await invalidateWorkflowCollections(queryClient);
      toast.success("Workflow created from file");
    },
    onError: async (error) => {
      if (workflowErrorWorkflowId(error)) {
        await invalidateWorkflowCollections(queryClient);
      }
    },
  });
}

export function useReviewDecisionMutation(workflowId: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ reviewId, decision }: { reviewId: string; decision: string }) =>
      submitReview(reviewId, decision),
    onSuccess: async () => {
      await invalidateWorkflowCollections(queryClient);
      await invalidateWorkflowDetail(queryClient, workflowId);
      toast.success("Review decision recorded");
    },
    onError: async (error) => {
      await invalidateWorkflowCollections(queryClient);
      await invalidateWorkflowDetail(
        queryClient,
        workflowErrorWorkflowId(error) ?? workflowId,
      );
    },
  });
}

type UploadWorkflowPayload = {
  file: File;
  options: Parameters<typeof uploadFileWorkflow>[1];
};

async function invalidateWorkflowCollections(queryClient: ReturnType<typeof useQueryClient>) {
  await queryClient.invalidateQueries({ queryKey: queryKeys.stats });
  await queryClient.invalidateQueries({ queryKey: ["workflow-summaries"] });
  await queryClient.invalidateQueries({ queryKey: ["review-summaries"] });
}

async function invalidateWorkflowDetail(
  queryClient: ReturnType<typeof useQueryClient>,
  workflowId: string | null,
) {
  if (!workflowId) return;
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: queryKeys.workflow(workflowId) }),
    queryClient.invalidateQueries({ queryKey: queryKeys.events(workflowId) }),
    queryClient.invalidateQueries({ queryKey: queryKeys.output(workflowId) }),
  ]);
}

export function workflowErrorMessage(error: unknown): string {
  return apiErrorMessage(error);
}

export function workflowErrorWorkflowId(error: unknown): string | null {
  return error instanceof ApiRequestError ? error.workflowId : null;
}

export function workflowErrorRequestId(error: unknown): string | null {
  return error instanceof ApiRequestError ? error.requestId : null;
}
