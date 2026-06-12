import type { RetrievalPackage } from "../../../types";

export function primaryRecommendedAction(packageData: RetrievalPackage) {
  return [...(packageData.recommended_actions ?? [])].sort(
    (left, right) => left.priority - right.priority,
  )[0] ?? null;
}
