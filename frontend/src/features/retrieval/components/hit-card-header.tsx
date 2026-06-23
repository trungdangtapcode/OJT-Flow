import { CheckCircle2, Clipboard } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
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
    <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
      <div className="min-w-0">
        <div className="flex items-baseline gap-2">
          <span className="text-[10px] font-bold uppercase text-muted-foreground">#{index + 1}</span>
          <h3 className="break-words text-sm font-bold leading-5">
            {evidence.source_id}
          </h3>
        </div>
        <div className="mt-0.5 flex flex-wrap gap-1 text-[11px] text-muted-foreground">
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
      <div className="flex flex-wrap items-center justify-end gap-1">
        <Badge variant="success">{formatConfidence(evidence.confidence)}</Badge>
        <Badge variant="muted">{formatScore(score)}</Badge>
        <Button
          aria-label={`Copy evidence for ${evidence.source_id}`}
          onClick={onCopyEvidenceReport}
          size="sm"
          type="button"
          variant="ghost"
        >
          {evidenceCopied ? (
            <CheckCircle2 className="h-3.5 w-3.5" />
          ) : (
            <Clipboard className="h-3.5 w-3.5" />
          )}
        </Button>
      </div>
    </div>
  );
}
