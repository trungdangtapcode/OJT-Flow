import { CheckCircle2, Clipboard } from "lucide-react";

import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";

export function JudgmentEvaluationCopyAction({
  copyEvaluationReport,
  evaluationCopied,
  evaluationReportJson,
}: {
  copyEvaluationReport: () => Promise<void>;
  evaluationCopied: boolean;
  evaluationReportJson: string | null;
}) {
  if (!evaluationReportJson) {
    return null;
  }

  return (
    <>
      <Button
        aria-label="Copy retrieval judgment evaluation report"
        onClick={() => void copyEvaluationReport()}
        size="sm"
        type="button"
        variant="outline"
      >
        {evaluationCopied ? (
          <CheckCircle2 className="h-4 w-4" />
        ) : (
          <Clipboard className="h-4 w-4" />
        )}
        {evaluationCopied ? "Copied" : "Copy evaluation JSON"}
      </Button>
      <HelpTooltip label="Judgment evaluation JSON report help">
        Copies server relevance metrics, local judgment coverage, stored-label summary,
        recommendations, and query-profile context for retrieval tuning notes.
      </HelpTooltip>
    </>
  );
}
