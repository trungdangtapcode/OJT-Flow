import { humanize } from "../../../lib/utils";
import type { RetrievalPackage } from "../../../types";
import { evidenceInterpretationCards } from "./evidence-interpretation-cards";
import {
  fallbackEvidenceStatus,
  fallbackEvidenceSummary,
} from "./evidence-interpretation-status";
import type { EvidenceInterpretationViewModel } from "./evidence-interpretation-types";
import {
  primaryEvidenceAction,
  supportStatusValue,
} from "./evidence-interpretation-values";

export function buildEvidenceInterpretationViewModel(
  packageData: RetrievalPackage,
): EvidenceInterpretationViewModel {
  const topHit = packageData.hits[0] ?? null;
  const primaryAction = primaryEvidenceAction(packageData);
  const requiredBuckets = packageData.evidence_buckets?.filter((bucket) => bucket.required) ?? [];
  const missingRequiredBuckets = requiredBuckets.filter((bucket) => bucket.hit_count === 0);
  const backend = packageData.interpretation ?? null;
  const supportStatus = supportStatusValue(
    backend?.support_status ?? topHit?.match_explanation?.support_status,
  );

  return {
    cards: evidenceInterpretationCards({
      backend,
      missingRequiredBuckets,
      packageData,
      primaryAction,
      requiredBuckets,
      topHit,
    }),
    status: backend ? humanize(backend.status) : fallbackEvidenceStatus(packageData, missingRequiredBuckets),
    summary: backend?.summary ?? fallbackEvidenceSummary(packageData, missingRequiredBuckets),
    supportStatus,
  };
}
