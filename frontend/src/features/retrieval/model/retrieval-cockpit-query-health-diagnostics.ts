import { humanize } from "../../../lib/utils";
import type { RetrievalCockpitQueryDiagnostic } from "./retrieval-cockpit-runtime";
import type { RetrievalCockpitQueryHealthItem } from "./retrieval-cockpit-query-health-types";

export function queryDiagnosticHealthItems(
  diagnostics: RetrievalCockpitQueryDiagnostic[],
): RetrievalCockpitQueryHealthItem[] {
  return diagnostics
    .filter((diagnostic) => diagnostic.severity !== "info")
    .map((diagnostic) => ({
      code: `diagnostic_${diagnostic.code}`,
      description: `${diagnostic.message} Action: ${diagnostic.suggestedAction}`,
      label:
        diagnostic.code === "overconstrained_metadata_filters"
          ? "Filter over-constraint"
          : humanize(diagnostic.code),
      status:
        diagnostic.severity === "error" || diagnostic.severity === "destructive"
          ? "blocked"
          : "review",
    }));
}
