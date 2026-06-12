import type { RetrievalPackage, RetrievalSearchPayload } from "../../../types";
import { queryAnalysisFromPackage } from "./retrieval-cockpit-runtime";
import { queryDiagnosticHealthItems } from "./retrieval-cockpit-query-health-diagnostics";
import { baseQueryHealthItems } from "./retrieval-cockpit-query-health-items";
import { queryHealthSignalsFromPackage } from "./retrieval-cockpit-query-health-signals";
import type { RetrievalCockpitQueryHealthItem } from "./retrieval-cockpit-query-health-types";

export function queryHealthItems(
  payload: RetrievalSearchPayload | null,
  packageData: RetrievalPackage,
): RetrievalCockpitQueryHealthItem[] {
  const analysis = queryAnalysisFromPackage(packageData);
  const signals = queryHealthSignalsFromPackage(payload, packageData);

  return [
    ...baseQueryHealthItems({ packageData, signals }),
    ...queryDiagnosticHealthItems(analysis.diagnostics),
  ];
}

export type { RetrievalCockpitQueryHealthItem };
