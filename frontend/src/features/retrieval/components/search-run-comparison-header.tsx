import { CheckCircle2, Clipboard } from "lucide-react";

import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { useCopyFeedback } from "./copy-feedback";
import { SearchRunComparisonStatusBadges } from "./search-run-comparison-status-badges";

const COMPARISON_REPORT_COPY_KEY = "comparison-report";

export function SearchRunComparisonHeader({
  copyTextToClipboard,
  qualitySummaryChanged,
  queryProfileChanged,
  reportJson,
  rulePackChanged,
  topSourceChanged,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  qualitySummaryChanged: boolean;
  queryProfileChanged: boolean;
  reportJson: string;
  rulePackChanged: boolean;
  topSourceChanged: boolean;
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const reportCopied = copiedKey === COMPARISON_REPORT_COPY_KEY;

  const copyReport = async () => {
    await copyTextToClipboard(reportJson);
    markCopied(COMPARISON_REPORT_COPY_KEY);
  };

  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
      <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
        Run comparison
        <HelpTooltip label="Run comparison help">
          Compares the currently displayed search package against the selected baseline run. Use this to tune query scope, filters, and retrieval policy, not to make clinical conclusions.
        </HelpTooltip>
      </div>
      <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
        <SearchRunComparisonStatusBadges
          qualitySummaryChanged={qualitySummaryChanged}
          queryProfileChanged={queryProfileChanged}
          rulePackChanged={rulePackChanged}
          topSourceChanged={topSourceChanged}
        />
        <Button
          aria-label="Copy retrieval comparison report"
          onClick={() => void copyReport()}
          size="sm"
          type="button"
          variant="outline"
        >
          {reportCopied ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <Clipboard className="h-4 w-4" />
          )}
          {reportCopied ? "Copied" : "Copy comparison JSON"}
        </Button>
        <HelpTooltip label="Comparison JSON report help">
          Copies active versus baseline search payloads, quality deltas, evidence changes, rank movement, and recommended tuning actions for offline review.
        </HelpTooltip>
      </div>
    </div>
  );
}
