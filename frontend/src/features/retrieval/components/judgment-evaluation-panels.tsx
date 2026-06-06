import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { cn, humanize } from "../../../lib/utils";
import type { RetrievalJudgmentEvaluationResult } from "../../../types";

export function EvaluationReadinessPanel({
  evaluation,
  formatCount,
  formatPercent,
}: {
  evaluation: RetrievalJudgmentEvaluationResult;
  formatCount: (count: number, singular: string, plural?: string) => string;
  formatPercent: (value: number) => string;
}) {
  const readiness = evaluation.evaluation_readiness;
  return (
    <div
      aria-label="Judgment evaluation readiness"
      className={cn(
        "grid gap-2 rounded-md border p-3 text-sm",
        evaluationReadinessClass(readiness.status),
      )}
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 font-black">
          {readiness.status === "ready" ? (
            <CheckCircle2 className="h-4 w-4 shrink-0" />
          ) : (
            <AlertTriangle className="h-4 w-4 shrink-0" />
          )}
          {readiness.label}
          <HelpTooltip label="Judgment readiness help">
            Readiness tells whether enough ranked hits have human labels for Precision@k, MAP@k, MRR@k, and nDCG@k to be useful for tuning.
          </HelpTooltip>
        </div>
        <Badge variant={evaluationReadinessVariant(readiness.status)}>
          {humanize(readiness.status)}
        </Badge>
      </div>
      <p className="break-words leading-6">{readiness.message}</p>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <Badge variant="muted">
          min {formatCount(readiness.min_judged_count, "judged hit")}
        </Badge>
        <Badge variant="muted">
          min coverage {formatPercent(readiness.min_coverage_at_k)}
        </Badge>
      </div>
    </div>
  );
}

export function JudgmentMetricCard({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "success" | "warning";
  value: string;
}) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2">
      <span className="text-xs font-bold text-muted-foreground">{label}</span>
      <Badge variant={tone}>{value}</Badge>
    </div>
  );
}

function evaluationReadinessVariant(
  status: string,
): "success" | "warning" | "destructive" | "muted" {
  if (status === "ready") return "success";
  if (status === "unlabeled") return "destructive";
  if (status === "low_confidence" || status === "usable_with_gaps") return "warning";
  return "muted";
}

function evaluationReadinessClass(status: string): string {
  if (status === "ready") return "border-emerald-200 bg-emerald-50 text-emerald-950";
  if (status === "unlabeled") return "border-red-200 bg-red-50 text-red-950";
  if (status === "low_confidence" || status === "usable_with_gaps") {
    return "border-amber-200 bg-amber-50 text-amber-950";
  }
  return "border-border bg-card text-card-foreground";
}
