import type { RetrievalSearchTask } from "../../../types";

export function firstRunnableLocalTask(tasks: RetrievalSearchTask[]) {
  return (
    tasks.find(
      (task) =>
        task.target === "local_corpus" &&
        task.action_type === "run_local_search" &&
        task.required,
    ) ??
    tasks.find(
      (task) => task.target === "local_corpus" && task.action_type === "run_local_search",
    ) ??
    null
  );
}

export function externalMedicalIndexTasks(tasks: RetrievalSearchTask[]) {
  return tasks.filter((task) => task.target === "external_medical_index");
}
