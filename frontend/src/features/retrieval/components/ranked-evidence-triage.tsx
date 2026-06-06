import { AlertTriangle, CheckCircle2, ClipboardCheck, SearchCheck } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import type { RetrievalQualitySummary } from "../../../types";

export type RankedEvidenceTriageView = {
  candidateCount: number;
  hitCount: number;
  isStale: boolean;
  judgedCount: number;
  qualitySummary: RetrievalQualitySummary | null;
  requiredBucketCount: number;
  coveredRequiredBucketCount: number;
};

export function RankedEvidenceTriage({ view }: { view: RankedEvidenceTriageView }) {
  const guidance = triageGuidance(view);
  const Icon = guidance.icon;
  return (
    <section
      aria-label="Ranked evidence triage"
      className="grid gap-3 rounded-md border border-border bg-card/80 p-3"
    >
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-2">
          <span className="mt-0.5 rounded-md bg-primary/10 p-1.5 text-primary">
            <Icon className="h-4 w-4" />
          </span>
          <div className="grid min-w-0 gap-1">
            <div className="text-xs font-black uppercase text-muted-foreground">
              Inspect first
            </div>
            <div className="break-words text-sm font-black leading-6">
              {guidance.headline}
            </div>
            <div className="break-words text-sm leading-6 text-muted-foreground">
              {guidance.detail}
            </div>
          </div>
        </div>
        <Badge variant={guidance.variant}>{guidance.state}</Badge>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <TriageFact label="Ranked hits" value={`${view.hitCount}/${view.candidateCount}`} />
        <TriageFact
          label="Required buckets"
          tone={
            view.requiredBucketCount &&
            view.coveredRequiredBucketCount < view.requiredBucketCount
              ? "warning"
              : "success"
          }
          value={
            view.requiredBucketCount
              ? `${view.coveredRequiredBucketCount}/${view.requiredBucketCount}`
              : "none"
          }
        />
        <TriageFact
          label="Judgments"
          tone={view.judgedCount ? "success" : "warning"}
          value={view.judgedCount ? `${view.judgedCount} labeled` : "unlabeled"}
        />
        <TriageFact
          label="Readiness"
          tone={qualityTone(view.qualitySummary)}
          value={
            view.qualitySummary
              ? `${view.qualitySummary.status} ${view.qualitySummary.score}/100`
              : "unavailable"
          }
        />
      </div>
    </section>
  );
}

function TriageFact({
  label,
  tone = "muted",
  value,
}: {
  label: string;
  tone?: "success" | "warning" | "muted" | "destructive";
  value: string;
}) {
  return (
    <div className="flex min-w-0 items-center justify-between gap-2 rounded-md border border-border bg-muted/20 px-3 py-2 text-xs">
      <span className="font-bold uppercase text-muted-foreground">{label}</span>
      <Badge variant={tone}>{value}</Badge>
    </div>
  );
}

function triageGuidance(view: RankedEvidenceTriageView): {
  detail: string;
  headline: string;
  icon: typeof AlertTriangle;
  state: string;
  variant: "success" | "warning" | "destructive" | "muted";
} {
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

function qualityTone(
  summary: RetrievalQualitySummary | null,
): "success" | "warning" | "muted" | "destructive" {
  if (!summary) return "muted";
  if (summary.status === "ready") return "success";
  if (summary.status === "blocked") return "destructive";
  return "warning";
}
