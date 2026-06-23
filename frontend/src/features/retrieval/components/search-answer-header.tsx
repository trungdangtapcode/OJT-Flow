import { CheckCircle2, Clipboard } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
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
    <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
      <div className="min-w-0">
        <div className="flex min-w-0 flex-wrap items-center gap-1.5">
          <Badge variant={answer.status.variant}>{answer.status.label}</Badge>
          {answer.qualityScore !== null ? (
            <Badge variant={answer.status.variant}>
              {answer.qualityScore}/100
            </Badge>
          ) : null}
          <Badge variant="muted">
            {formatSearchAnswerCount(hitCount, "hit")}
          </Badge>
        </div>
        <div className="mt-1.5 max-w-4xl break-words text-sm font-bold leading-6">
          {answer.remediation}
        </div>
      </div>
      <Button
        aria-label="Copy answer"
        onClick={onCopyReport}
        size="sm"
        type="button"
        variant="ghost"
      >
        {copied ? (
          <CheckCircle2 className="h-3.5 w-3.5" />
        ) : (
          <Clipboard className="h-3.5 w-3.5" />
        )}
      </Button>
    </div>
  );
}
