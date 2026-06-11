import type { RetrievalPackage } from "../../../types";
import {
  clinicalContextItem,
  querySpecificityItem,
  readinessItem,
  resultCoverageItem,
  safetySignalsItem,
  searchScopeItem,
} from "./retrieval-cockpit-query-health-item-builders";
import type {
  RetrievalCockpitQueryHealthItem,
} from "./retrieval-cockpit-query-health-types";
import type {
  RetrievalCockpitQueryHealthSignals,
} from "./retrieval-cockpit-query-health-signals";

export function baseQueryHealthItems({
  packageData,
  signals,
}: {
  packageData: RetrievalPackage;
  signals: RetrievalCockpitQueryHealthSignals;
}): RetrievalCockpitQueryHealthItem[] {
  return [
    querySpecificityItem(signals),
    clinicalContextItem(signals),
    searchScopeItem(signals),
    resultCoverageItem(signals),
    readinessItem({ packageData, signals }),
    safetySignalsItem(signals),
  ];
}
