import { AlertTriangle, BrainCircuit, CheckCircle2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { cn, humanize } from "../../../lib/utils";
import type { EvidenceSupportMatrixRowView } from "./evidence-support-matrix";

type EvidenceSupportStatus = EvidenceSupportMatrixRowView["supportStatus"];

export type EvidenceUseGuidanceView = {
  action: string;
  reasons: string[];
  status: EvidenceSupportStatus;
  title: string;
};

export type EvidenceUsabilitySummaryView = {
  checks: string[];
  headline: string;
  limitation: string;
  recommendation: string;
  status: EvidenceSupportStatus;
};

export type HitMatchExplanationView = {
  aspectLabels: string[];
  bucketLabels: string[];
  conceptLabels: string[];
  matchedTerms: string[];
  provenanceCount: number;
  rankingSignalCount: number;
  supportStatus: EvidenceSupportStatus;
  topScoreDriver: string | null;
};

export function EvidenceUsabilitySummaryPanel({
  summary,
}: {
  summary: EvidenceUsabilitySummaryView;
}) {
  return (
    <section
      aria-label="Evidence usability summary"
      className="grid gap-2 rounded-md border border-border bg-muted/20 p-2 text-sm"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <div className="grid min-w-0 gap-1">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Usability summary
          </div>
          <div className="break-words font-semibold">{summary.headline}</div>
        </div>
        <Badge variant={supportStatusBadgeVariant(summary.status)}>
          {humanize(summary.status)}
        </Badge>
      </div>
      <div className="grid gap-1.5 sm:grid-cols-2">
        <div className="rounded-md border border-border bg-card/70 px-2 py-1.5">
          <div className="text-[11px] font-black uppercase text-muted-foreground">
            Recommendation
          </div>
          <div className="mt-1 break-words font-semibold">
            {summary.recommendation}
          </div>
        </div>
        <div className="rounded-md border border-border bg-card/70 px-2 py-1.5">
          <div className="text-[11px] font-black uppercase text-muted-foreground">
            Limitation
          </div>
          <div className="mt-1 break-words text-muted-foreground">
            {summary.limitation}
          </div>
        </div>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {summary.checks.map((check) => (
          <Badge className="max-w-full break-words" key={check} variant="muted">
            {check}
          </Badge>
        ))}
      </div>
    </section>
  );
}

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

export function HitMatchExplanationPanel({
  explanation,
  formatCount,
}: {
  explanation: HitMatchExplanationView;
  formatCount: (count: number, singular: string) => string;
}) {
  return (
    <div
      aria-label="Why this evidence matched"
      className="grid gap-2 rounded-md border border-border bg-muted/20 p-2"
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2 text-xs font-bold uppercase text-muted-foreground">
          <BrainCircuit className="h-3.5 w-3.5 shrink-0" />
          <span>Why this matched</span>
        </div>
        <Badge variant={supportStatusBadgeVariant(explanation.supportStatus)}>
          {humanize(explanation.supportStatus)}
        </Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <MatchExplanationMetric
          label="Top driver"
          value={explanation.topScoreDriver ?? "not reported"}
        />
        <MatchExplanationMetric
          label="Evidence pack"
          value={
            explanation.bucketLabels.length
              ? explanation.bucketLabels.join(", ")
              : "unbucketed"
          }
        />
        <MatchExplanationMetric
          label="Terms"
          value={
            explanation.matchedTerms.length
              ? explanation.matchedTerms.join(", ")
              : "no exact terms"
          }
        />
        <MatchExplanationMetric
          label="Traceability"
          value={`${formatCount(explanation.provenanceCount, "provenance field")}, ${formatCount(
            explanation.rankingSignalCount,
            "ranking signal",
          )}`}
        />
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {explanation.conceptLabels.map((label) => (
          <Badge className="max-w-full break-words" key={`concept-${label}`} variant="muted">
            {label}
          </Badge>
        ))}
        {explanation.aspectLabels.map((label) => (
          <Badge className="max-w-full break-words" key={`aspect-${label}`} variant="muted">
            {label}
          </Badge>
        ))}
        {!explanation.conceptLabels.length && !explanation.aspectLabels.length ? (
          <span className="text-xs font-semibold text-muted-foreground">
            No concept or query-aspect grounding was reported for this hit.
          </span>
        ) : null}
      </div>
    </div>
  );
}

function MatchExplanationMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-card/70 px-2 py-1.5 text-xs">
      <span className="font-bold text-muted-foreground">{label}</span>
      <span className="min-w-0 break-words font-semibold">{value}</span>
    </div>
  );
}

function supportStatusBadgeVariant(
  status: EvidenceSupportStatus,
): "success" | "warning" | "destructive" {
  if (status === "strong") return "success";
  if (status === "partial") return "warning";
  return "destructive";
}
