import type { RetrievalJudgmentPayload } from "../../../types";
import { relevanceJudgmentRating } from "./retrieval-judgment-labels";
import type { SetHitJudgmentInput } from "./retrieval-judgment-types";

export function retrievalJudgmentPayload({
  evidence,
  queryText,
  runId,
  searchSignature,
  value,
}: SetHitJudgmentInput): RetrievalJudgmentPayload {
  return {
    query: queryText,
    evidence_id: evidence.evidence_id,
    source_id: evidence.source_id,
    source_type: evidence.source_type,
    source_version: evidence.source_version ?? null,
    value,
    rating: relevanceJudgmentRating(value),
    run_id: runId,
    search_signature: searchSignature,
    metadata: {
      trust_level: evidence.trust_level,
      review_surface: "retrieval_console",
    },
  };
}
