import type { RetrievalPackage, RetrievalSearchPayload } from "../../../types";
import { searchHintsFromPackage } from "./search-answer-hints";
import { fallbackInterpretation } from "./search-answer-interpretation";
import type { SearchAnswerStatus } from "./search-answer-types";

export function searchAnswerReportFromPackage(
  packageData: RetrievalPackage,
  submittedSearchPayload: RetrievalSearchPayload | null,
  summary: {
    missingBucketLabels: string[];
    remediation: string;
    status: SearchAnswerStatus;
    warningCount: number;
  },
) {
  const topHit = packageData.hits[0] ?? null;
  return {
    report_type: "retrieval_search_answer",
    version: 1,
    generated_at: new Date().toISOString(),
    query: submittedSearchPayload?.query ?? null,
    status: summary.status.label,
    remediation_summary: summary.remediation,
    interpretation: packageData.interpretation ?? fallbackInterpretation(packageData),
    standard_search_plan: packageData.standard_search_plan ?? null,
    medical_search_hints: searchHintsFromPackage(packageData),
    diversity: packageData.diversity ?? null,
    readiness: packageData.quality_summary,
    warnings: {
      count: summary.warningCount,
      trace: packageData.trace.warnings,
      coverage: packageData.coverage?.warnings ?? [],
    },
    required_support: {
      missing_buckets: summary.missingBucketLabels,
      buckets: packageData.evidence_buckets ?? [],
    },
    top_evidence: topHit
      ? {
          evidence_id: topHit.evidence.evidence_id,
          source_id: topHit.evidence.source_id,
          source_type: topHit.evidence.source_type,
          trust_level: topHit.evidence.trust_level,
          claim: topHit.evidence.claim,
          score: topHit.score,
          match_explanation: topHit.match_explanation ?? null,
        }
      : null,
    recommended_actions: (packageData.recommended_actions ?? []).slice(0, 6),
  };
}
