import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { cn, humanize } from "../../../lib/utils";
import { supportStatusBadgeVariant } from "./evidence-support-status";
import type { EvidenceUseGuidanceView } from "./evidence-interpretation-guidance-types";

export function EvidenceUseGuidancePanel({
  guidance,
}: {
  guidance: EvidenceUseGuidanceView;
}) {
  const Icon = guidance.status === "strong" ? CheckCircle2 : AlertTriangle;
  return (
    <div
      aria-label="Evidence interpretation guidance"
      className={cn(
        "grid gap-2 rounded-md border p-2 text-sm",
        guidance.status === "strong"
          ? "border-emerald-200 bg-emerald-50 text-emerald-950"
          : guidance.status === "partial"
            ? "border-amber-200 bg-amber-50 text-amber-950"
            : "border-red-200 bg-red-50 text-red-950",
      )}
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex min-w-0 items-center gap-2 font-black">
          <Icon className="h-4 w-4 shrink-0" />
          <span>{guidance.title}</span>
          <HelpTooltip label="Evidence interpretation help">
            This is a data-derived operator guide for the evidence card. It summarizes whether the hit has enough terms, provenance, medical grounding, and judgment state for review.
          </HelpTooltip>
        </div>
        <Badge variant={supportStatusBadgeVariant(guidance.status)}>
          {humanize(guidance.status)}
        </Badge>
      </div>
      <div className="break-words font-semibold leading-6">{guidance.action}</div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {guidance.reasons.map((reason) => (
          <Badge className="max-w-full break-words" key={reason} variant="muted">
            {reason}
          </Badge>
        ))}
      </div>
    </div>
  );
}
