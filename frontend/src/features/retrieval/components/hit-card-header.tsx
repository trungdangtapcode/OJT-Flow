import { CheckCircle2, Clipboard } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { humanize } from "../../../lib/utils";
import type { RetrievalHit } from "../../../types";

export function HitCardHeader({
  evidence,
  evidenceCopied,
  formatConfidence,
  formatScore,
  index,
  onCopyEvidenceReport,
  score,
}: {
  evidence: RetrievalHit["evidence"];
  evidenceCopied: boolean;
  formatConfidence: (confidence: number | null | undefined) => string;
  formatScore: (score: number) => string;
  index: number;
  onCopyEvidenceReport: () => void;
  score: number;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        <div className="text-xs font-bold uppercase text-muted-foreground">
          Rank {index + 1}
        </div>
        <h3 className="mt-1 break-words text-base font-extrabold leading-5">
          {evidence.source_id}
        </h3>
        <div className="mt-1 flex flex-wrap gap-1.5 text-xs font-bold text-muted-foreground">
          <span>{humanize(evidence.source_type)}</span>
          <span>/</span>
          <span>{humanize(evidence.trust_level)}</span>
          {String(evidence.locator.standard_system ?? "") ? (
            <>
              <span>/</span>
              <span>{String(evidence.locator.standard_system)}</span>
            </>
          ) : null}
        </div>
      </div>
      <div className="flex flex-wrap justify-end gap-1.5">
        <Badge variant="success">{formatConfidence(evidence.confidence)}</Badge>
        <Badge variant="muted">score {formatScore(score)}</Badge>
        <Button
          aria-label={`Copy evidence report for ${evidence.source_id}`}
          onClick={onCopyEvidenceReport}
          size="sm"
          type="button"
          variant="outline"
        >
          {evidenceCopied ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <Clipboard className="h-4 w-4" />
          )}
          {evidenceCopied ? "Copied" : "Copy evidence JSON"}
        </Button>
        <HelpTooltip label="Evidence JSON report help">
          Copies this evidence hit with identity, score details, provenance, match explanation, bucket support, locators, and snippet context.
        </HelpTooltip>
      </div>
    </div>
  );
}
