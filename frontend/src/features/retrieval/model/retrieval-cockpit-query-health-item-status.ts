import type {
  RetrievalCockpitQueryHealthSignals,
} from "./retrieval-cockpit-query-health-signals";
import type {
  RetrievalCockpitQueryHealthItem,
} from "./retrieval-cockpit-query-health-types";

type QueryHealthStatus = RetrievalCockpitQueryHealthItem["status"];

export function querySpecificityStatus(
  signals: RetrievalCockpitQueryHealthSignals,
): QueryHealthStatus {
  return signals.queryTerms.length >= 3 ? "ok" : "review";
}

export function clinicalContextStatus(
  signals: RetrievalCockpitQueryHealthSignals,
): QueryHealthStatus {
  return signals.hasClinicalContext ? "ok" : "review";
}

export function searchScopeStatus(
  signals: RetrievalCockpitQueryHealthSignals,
): QueryHealthStatus {
  return signals.exactSource || signals.filterCount >= 3 ? "review" : "info";
}

export function resultCoverageStatus(
  signals: RetrievalCockpitQueryHealthSignals,
): QueryHealthStatus {
  if (signals.hitCount === 0) {
    return "blocked";
  }
  return signals.hitCount < Math.min(signals.topK, 3) ? "review" : "ok";
}

export function readinessStatus(
  signals: RetrievalCockpitQueryHealthSignals,
): QueryHealthStatus {
  if (signals.qualityStatus === "ready") {
    return "ok";
  }
  if (signals.qualityStatus === "blocked") {
    return "blocked";
  }
  return signals.qualityStatus ? "review" : "info";
}

export function safetySignalsStatus(
  signals: RetrievalCockpitQueryHealthSignals,
): QueryHealthStatus {
  return signals.warningCount ? "review" : "ok";
}
