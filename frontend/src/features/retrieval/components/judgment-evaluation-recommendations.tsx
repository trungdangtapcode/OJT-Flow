import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalJudgmentEvaluationResult } from "../../../types";
import type { BadgeVariant } from "./judgment-evaluation-types";

export function EvaluationRecommendationList({
  evaluation,
  qualitySignalBadgeVariant,
}: {
  evaluation: RetrievalJudgmentEvaluationResult;
  qualitySignalBadgeVariant: (severity: string) => BadgeVariant;
}) {
  if (!evaluation.recommendations.length) return null;
  return (
    <div className="grid gap-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Evaluation recommendations
      </div>
      {evaluation.recommendations.map((recommendation) => {
        const warning =
          recommendation.severity === "warning" ||
          recommendation.severity === "destructive" ||
          recommendation.severity === "error";
        return (
          <div
            className="grid gap-1.5 rounded-md border border-border bg-card p-2 text-xs"
            key={recommendation.rule_id}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="flex min-w-0 items-center gap-1.5">
                {warning ? (
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-600" />
                ) : (
                  <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
                )}
                <span className="break-words font-bold">
                  {humanize(recommendation.rule_id)}
                </span>
              </span>
              <Badge variant={qualitySignalBadgeVariant(recommendation.severity)}>
                {recommendation.metric}
              </Badge>
            </div>
            <div className="break-words text-muted-foreground">
              {recommendation.message}
            </div>
            <div className="break-words font-semibold text-foreground">
              {recommendation.suggested_action}
            </div>
            {recommendation.evidence_ids.length ? (
              <div className="flex min-w-0 flex-wrap gap-1">
                {recommendation.evidence_ids.slice(0, 4).map((evidenceId) => (
                  <code
                    className="max-w-full break-words rounded bg-muted px-1.5 py-1 font-mono text-[11px]"
                    key={`${recommendation.rule_id}-${evidenceId}`}
                  >
                    {evidenceId}
                  </code>
                ))}
                {recommendation.evidence_ids.length > 4 ? (
                  <span className="text-xs font-semibold text-muted-foreground">
                    +{recommendation.evidence_ids.length - 4} more
                  </span>
                ) : null}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
