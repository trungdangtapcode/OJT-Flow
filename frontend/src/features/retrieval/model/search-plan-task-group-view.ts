import type { RetrievalSearchTask } from "../../../types";
import { orderedSearchPlanTasks } from "./search-plan-tasks";

export function searchPlanTaskGroupView(tasks: RetrievalSearchTask[]) {
  const orderedTasks = orderedSearchPlanTasks(tasks);
  const visibleTasks = orderedTasks.slice(0, 4);
  const remainingTasks = orderedTasks.slice(4);
  const requiredTaskCount = tasks.filter((task) => task.required).length;
  const optionalTaskCount = tasks.length - requiredTaskCount;

  return {
    optionalTaskCount,
    orderedTasks,
    remainingTasks,
    requiredTaskCount,
    visibleTasks,
  };
}
