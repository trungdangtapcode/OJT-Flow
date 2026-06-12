import type {
  QueryAnalysisStack,
  SearchPlanCoverageStack,
} from "./retrieval-query-analysis-types";
import { uniqueValues } from "./retrieval-query-analysis-coercion";

export function searchPlanCoverageSummary(
  analysis: QueryAnalysisStack,
): SearchPlanCoverageStack {
  if (analysis.planCoverageSummary) return analysis.planCoverageSummary;
  const localTasks = analysis.retrievalTasks.filter((task) => task.target === "local_corpus");
  const externalTasks = analysis.retrievalTasks.filter(
    (task) => task.target === "external_medical_index",
  );
  const standards = uniqueValues([
    ...analysis.standards,
    ...analysis.retrievalTasks.flatMap((task) => task.standards),
  ]);
  const filterKeys = new Set<string>();
  for (const suggestion of analysis.filterSuggestions) {
    filterKeys.add(`${suggestion.field}:${suggestion.value}`);
  }
  for (const task of analysis.retrievalTasks) {
    for (const [field, value] of Object.entries(task.suggested_filters)) {
      filterKeys.add(`${field}:${value}`);
    }
  }
  const warnings = uniqueValues([
    ...analysis.diagnostics
      .filter((diagnostic) => diagnostic.severity !== "info")
      .map((diagnostic) => diagnostic.code),
    ...analysis.retrievalTasks.flatMap((task) => task.warnings),
  ]);
  const requiredLocalTaskCount = localTasks.filter((task) => task.required).length;
  const ready = requiredLocalTaskCount > 0 && standards.length > 0;
  return {
    externalTaskCount: externalTasks.length,
    filterCount: filterKeys.size,
    localTaskCount: localTasks.length,
    ready,
    requiredLocalTaskCount,
    standards,
    nextAction: fallbackPlanCoverageNextAction({
      externalTaskCount: externalTasks.length,
      filterCount: filterKeys.size,
      ready,
      requiredLocalTaskCount,
      standardCount: standards.length,
    }),
    summary: `${requiredLocalTaskCount}/${localTasks.length} required local task(s), ${externalTasks.length} external follow-up(s), ${standards.length} standard(s), and ${filterKeys.size} suggested filter(s).`,
    warnings,
  };
}

function fallbackPlanCoverageNextAction({
  externalTaskCount,
  filterCount,
  ready,
  requiredLocalTaskCount,
  standardCount,
}: {
  externalTaskCount: number;
  filterCount: number;
  ready: boolean;
  requiredLocalTaskCount: number;
  standardCount: number;
}): string {
  if (!ready && standardCount === 0) {
    return "Add a healthcare standard, schema, resource type, field list, or clinical domain.";
  }
  if (!ready && requiredLocalTaskCount === 0) {
    return "Refine the query until the plan has at least one required local corpus task.";
  }
  if (filterCount > 0) return "Review suggested filters, then run the local evidence search.";
  if (externalTaskCount > 0) {
    return "Run local evidence search, then inspect external follow-up tasks if coverage is incomplete.";
  }
  return "Run local evidence search.";
}
