import { CheckCircle2, Clipboard } from "lucide-react";

import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { useCopyFeedback } from "./copy-feedback";

const COCKPIT_REPORT_COPY_KEY = "cockpit-report";

export function SearchCockpitCopyAction({
  copyTextToClipboard,
  reportJson,
}: {
  copyTextToClipboard: (text: string) => Promise<void>;
  reportJson: string;
}) {
  const { copiedKey, markCopied } = useCopyFeedback();
  const reportCopied = copiedKey === COCKPIT_REPORT_COPY_KEY;

  const copyReport = async () => {
    await copyTextToClipboard(reportJson);
    markCopied(COCKPIT_REPORT_COPY_KEY);
  };

  return (
    <>
      <Button
        aria-label="Copy retrieval cockpit report"
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
        {reportCopied ? "Copied" : "Copy cockpit JSON"}
      </Button>
      <HelpTooltip label="Cockpit JSON report help">
        Copies the current retrieval package summary: submitted payload, route, ranking stack, readiness, evidence buckets, compact hits, actions, and rule-pack fingerprints.
      </HelpTooltip>
    </>
  );
}
