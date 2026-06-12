import type { RetrievalPackage } from "../../../types";
import {
  clinicalContextDescription,
  clinicalContextStatus,
  querySpecificityDescription,
  querySpecificityStatus,
  readinessDescription,
  readinessStatus,
  resultCoverageDescription,
  resultCoverageStatus,
  safetySignalsDescription,
  safetySignalsStatus,
  searchScopeDescription,
  searchScopeStatus,
} from "./retrieval-cockpit-query-health-item-policy";
import type {
  RetrievalCockpitQueryHealthSignals,
} from "./retrieval-cockpit-query-health-signals";
import type {
  RetrievalCockpitQueryHealthItem,
} from "./retrieval-cockpit-query-health-types";

export function querySpecificityItem(
  signals: RetrievalCockpitQueryHealthSignals,
): RetrievalCockpitQueryHealthItem {
  return {
    code: "query_specificity",
    description: querySpecificityDescription(signals),
    label: "Query specificity",
    status: querySpecificityStatus(signals),
  };
}

export function clinicalContextItem(
  signals: RetrievalCockpitQueryHealthSignals,
): RetrievalCockpitQueryHealthItem {
  return {
    code: "clinical_context",
    description: clinicalContextDescription(signals),
    label: "Clinical context",
    status: clinicalContextStatus(signals),
  };
}

export function searchScopeItem(
  signals: RetrievalCockpitQueryHealthSignals,
): RetrievalCockpitQueryHealthItem {
  return {
    code: "scope",
    description: searchScopeDescription(signals),
    label: "Search scope",
    status: searchScopeStatus(signals),
  };
}

export function resultCoverageItem(
  signals: RetrievalCockpitQueryHealthSignals,
): RetrievalCockpitQueryHealthItem {
  return {
    code: "result_coverage",
    description: resultCoverageDescription(signals),
    label: "Result coverage",
    status: resultCoverageStatus(signals),
  };
}

export function readinessItem({
  packageData,
  signals,
}: {
  packageData: RetrievalPackage;
  signals: RetrievalCockpitQueryHealthSignals;
}): RetrievalCockpitQueryHealthItem {
  return {
    code: "readiness",
    description: readinessDescription({ packageData, signals }),
    label: "Readiness",
    status: readinessStatus(signals),
  };
}

export function safetySignalsItem(
  signals: RetrievalCockpitQueryHealthSignals,
): RetrievalCockpitQueryHealthItem {
  return {
    code: "safety",
    description: safetySignalsDescription(signals),
    label: "Safety signals",
    status: safetySignalsStatus(signals),
  };
}
