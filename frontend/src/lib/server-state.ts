import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  ApiRequestError,
  API_BASE_URL,
  chatWithAssistant,
  createWorkflow,
  deleteRetrievalJudgment,
  getExtractorInventory,
  getRetrievalJudgmentSummary,
  getRetrievalIntegrity,
  getRetrievalSearchOptions,
  getRuntimeConfig,
  getRuntimeHealth,
  getRuntimeReadiness,
  getWorkflow,
  getWorkflowOutput,
  getWorkflowStats,
  listAssistantTools,
  listRetrievalJudgments,
  listRetrievalPresets,
  listRetrievalSources,
  listReviewSummaries,
  listSchemas,
  listWorkflowEvents,
  listWorkflowSummaries,
  reindexRetrieval,
  searchRetrieval,
  submitReview,
  updateRuntimeAssistantSettings,
  updateRuntimeRetrievalSettings,
  upsertRetrievalJudgment,
  uploadFileWorkflow,
} from "../api";
import type {
  AssistantChatPayload,
  RetrievalJudgmentPayload,
  RetrievalReindexPayload,
  RetrievalSearchPayload,
  RuntimeAssistantSettingsPayload,
  RuntimeRetrievalSettingsPayload,
  StartWorkflowPayload,
} from "../types";

export const queryKeys = {
  stats: ["workflow-stats"] as const,
  workflowSummaries: (params: Record<string, unknown>) => ["workflow-summaries", params] as const,
  reviewSummaries: (params: Record<string, unknown>) => ["review-summaries", params] as const,
  workflow: (workflowId: string | null) => ["workflow", workflowId] as const,
  output: (workflowId: string | null) => ["workflow-output", workflowId] as const,
  events: (workflowId: string | null) => ["workflow-events", workflowId] as const,
  schemas: ["schemas"] as const,
  retrievalSources: ["retrieval-sources"] as const,
  retrievalJudgments: (params: Record<string, unknown>) =>
    ["retrieval-judgments", params] as const,
  retrievalJudgmentSummary: (params: Record<string, unknown>) =>
    ["retrieval-judgment-summary", params] as const,
  retrievalSearchOptions: ["retrieval-search-options"] as const,
  retrievalIntegrity: (params: Record<string, unknown>) => ["retrieval-integrity", params] as const,
  extractors: ["extractors"] as const,
  health: ["runtime-health"] as const,
  runtimeConfig: ["runtime-config"] as const,
  runtimeReadiness: ["runtime-readiness"] as const,
  assistantTools: ["assistant-tools"] as const,
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

export function useRuntimeHealthQuery() {
  return useQuery({ queryKey: queryKeys.health, queryFn: getRuntimeHealth });
}

export function useRuntimeConfigQuery() {
  return useQuery({ queryKey: queryKeys.runtimeConfig, queryFn: getRuntimeConfig });
}

export function useRuntimeReadinessQuery() {
  return useQuery({ queryKey: queryKeys.runtimeReadiness, queryFn: getRuntimeReadiness });
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

export function useRetrievalIntegrityQuery(params: {
  include_seeded: boolean;
  include_corpus: boolean;
}) {
  return useQuery({
    queryKey: queryKeys.retrievalIntegrity(params),
    queryFn: () => getRetrievalIntegrity(params),
  });
}

export function useRetrievalSearchMutation() {
  return useMutation({
    mutationFn: (payload: RetrievalSearchPayload) => searchRetrieval(payload),
  });
}

export function useRetrievalJudgmentsQuery(params: {
  query?: string | null;
  run_id?: string | null;
  evidence_id?: string | null;
  limit?: number;
}) {
  return useQuery({
    enabled: Boolean(params.query || params.run_id || params.evidence_id),
    queryKey: queryKeys.retrievalJudgments(params),
    queryFn: () => listRetrievalJudgments(params),
  });
}

export function useRetrievalJudgmentSummaryQuery(params: {
  query?: string | null;
  limit?: number;
}) {
  return useQuery({
    enabled: Boolean(params.query),
    queryKey: queryKeys.retrievalJudgmentSummary(params),
    queryFn: () => getRetrievalJudgmentSummary(params),
  });
}

export function useRetrievalJudgmentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RetrievalJudgmentPayload) => upsertRetrievalJudgment(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["retrieval-judgments"] });
      await queryClient.invalidateQueries({ queryKey: ["retrieval-judgment-summary"] });
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

export function useAssistantToolsQuery() {
  return useQuery({ queryKey: queryKeys.assistantTools, queryFn: listAssistantTools });
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
  return error instanceof Error ? error.message : String(error);
}

export function workflowErrorWorkflowId(error: unknown): string | null {
  return error instanceof ApiRequestError ? error.workflowId : null;
}
