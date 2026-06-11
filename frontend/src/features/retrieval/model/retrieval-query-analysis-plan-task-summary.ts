import type { RetrievalPlanTaskSummary } from "../../../types";
import type { QueryAnalysisStack } from "./retrieval-query-analysis-types";

export function searchPlanTaskSummary(
  analysis: QueryAnalysisStack,
): RetrievalPlanTaskSummary {
  if (analysis.planTaskSummary) return analysis.planTaskSummary;
  const runnableLocal = analysis.retrievalTasks.filter(
    (task) => task.target === "local_corpus" && task.action_type === "run_local_search",
  );
  const requiredRunnableLocal = runnableLocal.filter((task) => task.required);
  const externalOpen = analysis.retrievalTasks.filter(
    (task) => task.target === "external_medical_index" && task.action_type === "open_external_url",
  );
  const externalCopy = analysis.retrievalTasks.filter(
    (task) => task.target === "external_medical_index" && task.action_type === "copy_query",
  );
  const blockedTasks = analysis.retrievalTasks.filter(
    (task) => !["run_local_search", "open_external_url", "copy_query"].includes(task.action_type),
  );
  const manualFollowupCount = externalOpen.length + externalCopy.length;
  return {
    total_task_count: analysis.retrievalTasks.length,
    runnable_local_count: runnableLocal.length,
    required_runnable_local_count: requiredRunnableLocal.length,
    external_open_count: externalOpen.length,
    external_copy_count: externalCopy.length,
    manual_followup_count: manualFollowupCount,
    blocked_task_count: blockedTasks.length,
    primary_action: requiredRunnableLocal.length
      ? "Run required local search tasks first, then review external follow-ups."
      : runnableLocal.length
        ? "Run the local search task, then review external follow-ups."
        : manualFollowupCount
          ? "Review external medical search follow-ups before trusting the plan."
          : "Add a more specific healthcare query before executing retrieval.",
    summary: `${runnableLocal.length} local runnable task(s), ${manualFollowupCount} external/manual follow-up(s), and ${blockedTasks.length} blocked task(s).`,
  };
}
