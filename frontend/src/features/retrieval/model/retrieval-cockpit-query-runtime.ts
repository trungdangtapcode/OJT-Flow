import { humanize } from "../../../lib/utils";
import type { RetrievalPackage } from "../../../types";
import type {
  RetrievalCockpitQueryAnalysisStack,
  RetrievalCockpitQueryDiagnostic,
} from "./retrieval-cockpit-runtime-types";
import {
  numberValue,
  optionalStringValue,
  recordValue,
  stringArrayValue,
  stringValue,
} from "./retrieval-runtime-values";

export function queryAnalysisFromPackage(
  packageData: RetrievalPackage,
): RetrievalCockpitQueryAnalysisStack {
  const queryAnalysis = recordValue(packageData.handoff_context.query_analysis);
  return {
    detectedConcepts: stringArrayValue(queryAnalysis.detected_concepts),
    diagnostics: queryDiagnosticsValue(queryAnalysis.diagnostics),
    expandedTerms: stringArrayValue(queryAnalysis.expanded_terms),
    queryAspects: queryAspectsValue(queryAnalysis.query_aspects),
    queryProfile: queryProfileValue(queryAnalysis.query_profile),
    standards: stringArrayValue(queryAnalysis.standards),
    strategy: stringValue(queryAnalysis.strategy, "unknown"),
    variantCount: stringArrayValue(queryAnalysis.query_variants).length,
  };
}

function queryAspectsValue(
  value: unknown,
): RetrievalCockpitQueryAnalysisStack["queryAspects"] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      aspectId: stringValue(item.aspect_id, "aspect"),
      label: stringValue(item.label, "Query aspect"),
      priority: numberValue(item.priority) ?? 100,
      question: stringValue(item.question, "Review this retrieval aspect."),
    }))
    .filter((item) => item.aspectId !== "aspect");
}

function queryProfileValue(
  value: unknown,
): RetrievalCockpitQueryAnalysisStack["queryProfile"] {
  const profile = recordValue(value);
  const profileId = optionalStringValue(profile.profile_id);
  if (!profileId) return null;
  return {
    complexity: stringValue(profile.complexity, "standard"),
    label: stringValue(profile.label, humanize(profileId)),
    retrievalMode: stringValue(profile.retrieval_mode, "hybrid"),
    route: stringValue(profile.route, profileId),
  };
}

function queryDiagnosticsValue(value: unknown): RetrievalCockpitQueryDiagnostic[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => recordValue(item))
    .map((item) => ({
      code: stringValue(item.code, "query_diagnostic"),
      message: stringValue(item.message, "Query diagnostic unavailable."),
      severity: stringValue(item.severity, "info"),
      suggestedAction: stringValue(item.suggested_action, "Review the retrieval query."),
    }))
    .filter((item) => item.code !== "query_diagnostic");
}
