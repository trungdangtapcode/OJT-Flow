import type { EvidenceInterpretationCard } from "./evidence-interpretation-types";
import type { EvidenceInterpretationCardContext } from "./evidence-interpretation-cards";
import {
  formatEvidenceInterpretationCount,
  stringArrayFromRecord,
  stringFromRecord,
} from "./evidence-interpretation-values";

export function topMatchInterpretationCard({
  backend,
  topHit,
}: Pick<EvidenceInterpretationCardContext, "backend" | "topHit">): EvidenceInterpretationCard {
  const topScoreDriver =
    backend?.top_score_driver ??
    stringFromRecord(topHit?.match_explanation, "top_score_driver") ??
    null;
  const matchedTerms = backend?.matched_terms?.length
    ? backend.matched_terms
    : topHit?.matched_terms.slice(0, 6) ?? [];
  const conceptLabels = backend?.concept_labels?.length
    ? backend.concept_labels
    : stringArrayFromRecord(topHit?.match_explanation, "concept_labels").slice(0, 4);
  const aspectLabels = backend?.aspect_labels?.length
    ? backend.aspect_labels
    : stringArrayFromRecord(topHit?.match_explanation, "aspect_labels").slice(0, 4);

  return {
    detail: topScoreDriver
      ? topScoreDriver
      : matchedTerms.length
        ? `Matched terms: ${matchedTerms.join(", ")}`
        : "No ranked evidence was returned for this request.",
    items: [
      conceptLabels.length ? `Concepts: ${conceptLabels.join(", ")}` : null,
      aspectLabels.length ? `Aspects: ${aspectLabels.join(", ")}` : null,
      topHit
        ? `${formatEvidenceInterpretationCount(Object.keys(topHit.evidence.locator ?? {}).length, "provenance field")} / ${formatEvidenceInterpretationCount(topHit.score_components?.length ?? 0, "ranking signal")}`
        : null,
    ].filter((item): item is string => Boolean(item)),
    label: "Why the top result matched",
    title: backend?.top_source_id ?? topHit?.evidence.source_id ?? "No ranked result",
  };
}
