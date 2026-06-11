import { CheckCircle2, Clipboard } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { SearchAnswerViewModel } from "../model/search-answer";
import { formatSearchAnswerCount } from "./search-answer-format";

export function SearchAnswerHeader({
  answer,
  copied,
  hitCount,
  onCopyReport,
}: {
  answer: SearchAnswerViewModel;
  copied: boolean;
  hitCount: number;
  onCopyReport: () => void;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <div className="text-xs font-black uppercase text-muted-foreground">
            Search answer
          </div>
          <Badge variant={answer.status.variant}>{answer.status.label}</Badge>
          {answer.qualityScore !== null ? (
            <Badge variant={answer.status.variant}>
              readiness {answer.qualityScore}/100
            </Badge>
          ) : null}
          <Badge variant="muted">
            {formatSearchAnswerCount(hitCount, "hit")}
          </Badge>
        </div>
        <div className="mt-2 max-w-4xl break-words text-base font-black leading-7">
          {answer.remediation}
        </div>
        <p className="mt-1 max-w-4xl text-sm leading-6 text-muted-foreground">
          This is an evidence retrieval summary for workflow operations. It explains source
          support and search quality; it is not clinical advice.
        </p>
      </div>
      <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
        <Button
          aria-label="Copy retrieval answer report"
          onClick={onCopyReport}
          size="sm"
          type="button"
          variant="outline"
        >
          {copied ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <Clipboard className="h-4 w-4" />
          )}
          {copied ? "Copied" : "Copy answer JSON"}
        </Button>
        <HelpTooltip label="Answer JSON report help">
          Copies the plain-language retrieval answer, readiness, warnings, top evidence, missing required buckets, and recommended backend actions.
        </HelpTooltip>
      </div>
    </div>
  );
}
