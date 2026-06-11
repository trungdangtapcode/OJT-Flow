import type {
  RetrievalHit,
  RetrievalRecommendedAction,
} from "../../../types";
import type {
  EvidenceHitMatchExplanation,
  EvidenceHitSignals,
  EvidenceProvenanceEntry,
  EvidenceSupportSummary,
  EvidenceUsabilitySummary,
  RetrievalEvidenceJudgment,
} from "./retrieval-evidence-types";
import { correctiveActionReportContext } from "./retrieval-evidence-corrective-actions-report";

export function evidenceReportFromHit({
  formatClaim,
  hit,
  judgment,
  matchExplanation,
  provenanceEntries,
  recommendedActions = [],
  signals,
  supportSummary,
  usabilitySummary,
}: {
  formatClaim: (claim: string) => string;
  hit: RetrievalHit;
  judgment: RetrievalEvidenceJudgment | null;
  matchExplanation: EvidenceHitMatchExplanation;
  provenanceEntries: EvidenceProvenanceEntry[];
  recommendedActions?: RetrievalRecommendedAction[];
  signals: EvidenceHitSignals;
  supportSummary: EvidenceSupportSummary;
  usabilitySummary: EvidenceUsabilitySummary;
}) {
  const correctiveActions = correctiveActionReportContext(hit, recommendedActions);
  return {
    report_type: "retrieval_evidence_hit",
    version: 1,
    generated_at: new Date().toISOString(),
    evidence: {
      evidence_id: hit.evidence.evidence_id,
      source_id: hit.evidence.source_id,
      source_type: hit.evidence.source_type,
      source_version: hit.evidence.source_version ?? null,
      trust_level: hit.evidence.trust_level,
      confidence: hit.evidence.confidence ?? null,
      claim: formatClaim(hit.evidence.claim),
    },
    support_summary: supportSummary,
    usability_summary: usabilitySummary,
    match_explanation: matchExplanation,
    ranking: {
      score: hit.score,
      lexical_score: hit.lexical_score,
      vector_score: hit.vector_score,
      rerank_score: hit.rerank_score,
      matched_terms: hit.matched_terms,
      score_components: signals.scoreComponents,
      ranking_boosts: signals.rankingBoostSignals,
    },
    grounding: {
      concept_matches: signals.conceptMatches,
      query_aspect_matches: signals.queryAspectMatches,
    },
    provenance: {
      summary: provenanceEntries,
      locator: hit.evidence.locator,
      source_locator: hit.source_locator,
    },
    corrective_actions: correctiveActions,
    snippet: hit.snippet,
  };
}
