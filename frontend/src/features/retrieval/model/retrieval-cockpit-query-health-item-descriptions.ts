import { humanize } from "../../../lib/utils";
import type { RetrievalPackage } from "../../../types";
import { formatCount } from "./retrieval-format";
import type {
  RetrievalCockpitQueryHealthSignals,
} from "./retrieval-cockpit-query-health-signals";

export function querySpecificityDescription(
  signals: RetrievalCockpitQueryHealthSignals,
) {
  return signals.queryTerms.length >= 3
    ? "The query has enough wording to guide hybrid search and reranking."
    : "The query is short. Add the data type, issue, standard, or expected field names if results look broad.";
}

export function clinicalContextDescription(
  signals: RetrievalCockpitQueryHealthSignals,
) {
  return signals.hasClinicalContext
    ? "Schema, format, resource, domain, standard, or field context is present."
    : "No clinical data context is set. Add schema, format, resource, fields, or standard filters for safer grounding.";
}

export function searchScopeDescription(
  signals: RetrievalCockpitQueryHealthSignals,
) {
  if (signals.exactSource) {
    return `Exact source scope is active for ${signals.exactSource}. Clear it before judging corpus-wide coverage.`;
  }
  if (signals.filterCount >= 3) {
    return "Multiple filters are active. If evidence is sparse, loosen scope before concluding no evidence exists.";
  }
  if (signals.filterCount > 0) {
    return "Some filters are active. Confirm they match the operational question.";
  }
  return "No source filters are active. This is good for discovery but may need narrowing for audit review.";
}

export function resultCoverageDescription(
  signals: RetrievalCockpitQueryHealthSignals,
) {
  if (signals.hitCount === 0) {
    return "No ranked evidence returned. Broaden scope, check source inventory, or apply backend recommendations.";
  }
  if (
    signals.hitCount < Math.min(signals.topK, 3) &&
    signals.candidateCount > signals.hitCount
  ) {
    return "Only a small ranked set survived selection. Inspect filters, readiness gaps, and reranker state.";
  }
  return `${signals.hitCount} ranked hit(s) from ${signals.candidateCount} candidate(s). Inspect readiness before individual claims.`;
}

export function readinessDescription({
  packageData,
  signals,
}: {
  packageData: RetrievalPackage;
  signals: RetrievalCockpitQueryHealthSignals;
}) {
  return signals.qualityStatus
    ? `Backend readiness is ${humanize(signals.qualityStatus)}${
        packageData.quality_summary ? ` at ${packageData.quality_summary.score}/100` : ""
      }.`
    : "No readiness score returned. Treat this package as unreviewed.";
}

export function safetySignalsDescription(
  signals: RetrievalCockpitQueryHealthSignals,
) {
  return signals.warningCount
    ? `${formatCount(signals.warningCount, "warning or safety signal", "warning or safety signals")} ${signals.warningCount === 1 ? "was" : "were"} reported. Review these before using the evidence downstream.`
    : "No retrieval warnings or safety flags were reported for this package.";
}
