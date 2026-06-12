import { humanize } from "../../../lib/utils";
import type { EvidenceInterpretationCard } from "./evidence-interpretation-types";
import type { EvidenceInterpretationCardContext } from "./evidence-interpretation-cards";

export function nextActionInterpretationCard({
  backend,
  primaryAction,
}: Pick<EvidenceInterpretationCardContext, "backend" | "primaryAction">): EvidenceInterpretationCard {
  return {
    detail:
      primaryAction?.description ??
      backend?.next_action_detail ??
      "Review backend interpretation and evidence details.",
    items: [
      primaryAction ? `Priority ${primaryAction.priority}` : null,
      primaryAction ? humanize(primaryAction.action_type) : null,
    ].filter((item): item is string => Boolean(item)),
    label: "Next action",
    title: primaryAction?.title ?? backend?.next_action_title ?? "Review evidence",
  };
}
