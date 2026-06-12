import { humanize } from "../../../lib/utils";
import type { RetrievalSearchTask } from "../../../types";

export function retrievalTaskExternalUrl(task: RetrievalSearchTask): string | null {
  if (task.action_type !== "open_external_url") return null;
  const url = optionalStringValue(task.metadata.url);
  if (!url || !/^https?:\/\//i.test(url)) return null;
  return url;
}

export function orderedSearchPlanTasks(tasks: RetrievalSearchTask[]): RetrievalSearchTask[] {
  return [...tasks].sort((left, right) => {
    if (left.required !== right.required) return left.required ? -1 : 1;
    return left.priority - right.priority || left.label.localeCompare(right.label);
  });
}

export function retrievalTaskClipboardText(task: RetrievalSearchTask): string {
  const url = retrievalTaskExternalUrl(task);
  return [
    `${task.required ? "required" : "optional"} P${task.priority}: ${task.label}`,
    `target: ${humanize(task.target)}`,
    `action: ${humanize(task.action_type)}`,
    `query: ${task.query}`,
    url ? `url: ${url}` : null,
  ]
    .filter(Boolean)
    .join("\n");
}

export function retrievalTaskActionLabel(task: RetrievalSearchTask): string {
  if (task.action_type === "run_local_search") return "Runs in OJTFlow";
  if (task.action_type === "open_external_url") return "Opens external source";
  return "Copies external query";
}

export function retrievalTaskActionDescription(task: RetrievalSearchTask): string {
  if (task.action_type === "run_local_search") {
    return "Runs the planned query against the governed local corpus and refreshes the ranked evidence package.";
  }
  if (task.action_type === "open_external_url") {
    return "Opens a trusted medical standards or literature page in a new tab. OJTFlow will not treat that page as indexed evidence until it is added to the corpus and reindexed.";
  }
  if (task.target === "external_medical_index") {
    return "Copies the planned external medical search query so it can be reviewed manually in the relevant source.";
  }
  return "Copies the planned query text for manual review before execution.";
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}
