import { AlertTriangle, CheckCircle2, ClipboardCheck, SearchCheck } from "lucide-react";

import type { RetrievalQualitySummary } from "../../../types";
import type {
  RankedEvidenceTriageGuidance,
  RankedEvidenceTriageView,
  TriageTone,
} from "./ranked-evidence-triage-types";

export function rankedEvidenceTriageGuidance(
  view: RankedEvidenceTriageView,
): RankedEvidenceTriageGuidance {
  if (view.isStale) {
    return {
      detail: "The query builder changed after this package was created. Rerun search before judging rank order.",
      headline: "Refresh search before using these rankings.",
      icon: AlertTriangle,
      state: "pending changes",
      variant: "warning",
    };
  }
  if (!view.hitCount) {
    return {
      detail: "Use the remediation panel to broaden scope, clear over-specific filters, or inspect source inventory.",
      headline: "No ranked evidence returned.",
      icon: SearchCheck,
      state: "no hits",
      variant: "destructive",
    };
  }
  if (
    view.requiredBucketCount &&
    view.coveredRequiredBucketCount < view.requiredBucketCount
  ) {
    return {
      detail: "Open readiness and evidence-bucket sections before relying on the top hit.",
      headline: "Required evidence buckets are missing.",
      icon: AlertTriangle,
      state: "support gaps",
      variant: "warning",
    };
  }
  if (!view.judgedCount) {
    return {
      detail: "Label the top evidence as relevant, partial, or not relevant so ranking quality becomes measurable.",
      headline: "Start by judging the first ranked hit.",
      icon: ClipboardCheck,
      state: "needs labels",
      variant: "warning",
    };
  }
  return {
    detail: "Review provenance, snippet matches, and judgment metrics before exporting or using the package downstream.",
    headline: "Evidence package is ready for review.",
    icon: CheckCircle2,
    state: "review ready",
    variant: "success",
  };
}

export function qualityTone(summary: RetrievalQualitySummary | null): TriageTone {
  if (!summary) return "muted";
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  return "warning";
}
