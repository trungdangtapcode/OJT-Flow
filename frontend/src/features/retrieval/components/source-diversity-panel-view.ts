import type { ComponentProps } from "react";

import type { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type {
  DiversitySelectionStack,
  DiversityStack,
} from "../model/retrieval-source-diversity-types";
import { formatCount } from "../model/retrieval-format";

type SourceDiversityBadgeVariant = ComponentProps<typeof Badge>["variant"];

export type SourceDiversityBadgeView = {
  label: string;
  variant: SourceDiversityBadgeVariant;
};

export function sourceDiversityDescription(enabled: boolean): string {
  if (enabled) {
    return "Final evidence was selected with source-aware diversity scoring so strong matches from repeated sources do not hide independent standards or policy evidence.";
  }

  return "Source diversity selection is disabled for this retrieval run; evidence follows score order only.";
}

export function sourceDiversityStateBadgeView(enabled: boolean): SourceDiversityBadgeView {
  return {
    label: enabled ? "enabled" : "disabled",
    variant: enabled ? "success" : "warning",
  };
}

export function sourceDiversityDuplicateBadgeView(
  duplicateSelectedSourceCount: number,
): SourceDiversityBadgeView {
  return {
    label: formatCount(duplicateSelectedSourceCount, "duplicate"),
    variant: duplicateSelectedSourceCount > 0 ? "warning" : "success",
  };
}

export function sourceDiversityModeLabel(diversity: DiversityStack): string {
  return humanize(diversity.selectionMode);
}

export function sourceDiversityBalanceWeightLabel(diversity: DiversityStack): string {
  return diversity.lambda === null ? "n/a" : diversity.lambda.toFixed(2);
}

export function visibleSourceDiversitySelections(
  diversity: DiversityStack,
): DiversitySelectionStack[] {
  return diversity.selectedHits
    .filter((selection) => selection.evidenceId && selection.sourceId)
    .slice(0, 4);
}
