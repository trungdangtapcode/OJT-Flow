export function buildAssistantWorkflowContextHref(workflowId: string) {
  return `/assistant?workflow_id=${encodeURIComponent(workflowId)}`;
}

export function buildAssistantRetrievalContextHref({
  hitCount,
  query,
  runId,
  strategy,
}: {
  hitCount: number;
  query: string;
  runId?: string | null;
  strategy?: string | null;
}) {
  const params = new URLSearchParams();
  params.set("retrieval_query", query);
  if (strategy) params.set("retrieval_strategy", strategy);
  if (runId) params.set("retrieval_run_id", runId);
  params.set("retrieval_hit_count", String(hitCount));
  return `/assistant?${params.toString()}`;
}
