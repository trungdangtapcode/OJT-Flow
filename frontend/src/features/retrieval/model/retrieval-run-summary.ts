import type { RetrievalPackage } from "../../../types";
import { diversityFromPackage } from "./retrieval-runtime-stack";
import { correctiveActionSummaryFromPackage } from "./retrieval-run-actions";
import {
  conceptGroundingSummariesFromPackage,
  coverageSummariesFromPackage,
  queryAspectSummariesFromPackage,
  queryProfileSummaryFromPackage,
} from "./retrieval-run-dimensions";
import {
  retrievalRulePacksFromPackage,
  rulePackFingerprint,
} from "./retrieval-run-rule-packs";
import type {
  RetrievalRunSummary,
  RetrievalSearchRun,
} from "./retrieval-run-summary-types";
import { optionalStringValue } from "./retrieval-run-summary-values";
import {
  qualitySummaryFingerprint,
  qualityWarningCount,
} from "./retrieval-run-quality-summary";

export function retrievalRunSummary(packageData: RetrievalPackage): RetrievalRunSummary {
  const rulePacks = retrievalRulePacksFromPackage(packageData);
  return {
    candidateCount: packageData.trace.candidates_seen,
    conceptGrounding: conceptGroundingSummariesFromPackage(packageData),
    correctiveActionSummary: correctiveActionSummaryFromPackage(packageData),
    coverage: coverageSummariesFromPackage(packageData),
    diversity: diversityFromPackage(packageData),
    hitCount: packageData.hits.length,
    qualitySummary: packageData.quality_summary ?? null,
    qualityWarningCount: qualityWarningCount(packageData.quality_signals ?? []),
    queryAspects: queryAspectSummariesFromPackage(packageData),
    queryProfile: queryProfileSummaryFromPackage(packageData),
    rulePackCount: rulePacks.length,
    rulePackFingerprint: rulePacks
      .map((pack) => `${pack.name}:${rulePackFingerprint(pack)}`)
      .join("|"),
    serverSignature: serverSearchSignatureFromPackage(packageData),
    remediationSummary:
      packageData.remediation_summary ??
      optionalStringValue(packageData.handoff_context.remediation_summary) ??
      null,
    topSourceId: packageData.hits[0]?.evidence.source_id ?? null,
    warningCount: packageData.trace.warnings.length,
  };
}

export function serverSearchSignatureFromPackage(packageData: RetrievalPackage): string | null {
  return optionalStringValue(packageData.handoff_context.search_signature);
}

export function evidenceIdsFromRun(run: RetrievalSearchRun): string[] {
  return run.packageData.hits.map((hit) => hit.evidence.evidence_id);
}

export { correctiveActionSummaryFromPackage };
export {
  qualitySummaryFingerprint,
  qualityWarningCount,
} from "./retrieval-run-quality-summary";
export {
  conceptGroundingKey,
  conceptGroundingSummariesFromPackage,
  coverageSummariesFromPackage,
  queryAspectSummariesFromPackage,
  queryProfileSummaryFromPackage,
} from "./retrieval-run-dimensions";
export {
  retrievalRulePacksFromPackage,
  rulePackFingerprint,
} from "./retrieval-run-rule-packs";
export type {
  ConceptGroundingSummary,
  CorrectiveActionSummary,
  QueryAspectSummary,
  QueryProfileSummary,
  RetrievalCoverageSummary,
  RetrievalRunSummary,
  RetrievalSearchRun,
} from "./retrieval-run-summary-types";
