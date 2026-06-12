import type { RetrievalPackage } from "../../../types";
import type { SearchAnswerStatus } from "./search-answer-types";

export function searchAnswerStatus(packageData: RetrievalPackage): SearchAnswerStatus {
  if (!packageData.hits.length) return { label: "No evidence hit", variant: "destructive" };
  const qualityStatus = packageData.quality_summary?.status;
  if (qualityStatus === "blocked") return { label: "Blocked", variant: "destructive" };
  if (qualityStatus === "review") return { label: "Needs review", variant: "warning" };
  if (packageData.trace.warnings.length) return { label: "Review warnings", variant: "warning" };
  return { label: "Evidence ready", variant: "success" };
}

export function searchAnswerFallbackRemediation(packageData: RetrievalPackage): string {
  const topAction = packageData.recommended_actions?.[0];
  if (topAction) return `${topAction.title}: ${topAction.description}`;
  const qualityAction = packageData.quality_summary?.top_action;
  if (qualityAction) return qualityAction;
  if (!packageData.hits.length) return "Broaden search scope or inspect source inventory.";
  return "Review the top evidence hit, readiness score, and source provenance before using this package.";
}
