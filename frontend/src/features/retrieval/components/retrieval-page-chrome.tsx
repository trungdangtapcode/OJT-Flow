import { Loader2, RefreshCw } from "lucide-react";

import { Button } from "../../../components/ui/button";
import { Notice } from "../../../components/ui/notice";
import {
  RetrievalSummaryStrip,
  type RetrievalSummaryStripViewModel,
} from "./retrieval-summary-strip";

export function RetrievalPageChrome({
  integrityError,
  onReindex,
  reindexError,
  reindexIsPending,
  reindexNotice,
  sourcesError,
  summary,
}: {
  integrityError: string | null;
  onReindex: () => void;
  reindexError: string | null;
  reindexIsPending: boolean;
  reindexNotice: string | null;
  sourcesError: string | null;
  summary: RetrievalSummaryStripViewModel;
}) {
  const hasError = sourcesError || reindexError || integrityError;

  return (
    <>
      <div className="flex min-w-0 items-center justify-between gap-2">
        <h1 className="text-lg font-bold tracking-tight text-foreground">Retrieval</h1>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">
            {summary.sourcesLoading ? "..." : `${summary.sourceCount} sources`}
          </span>
          <Button
            disabled={reindexIsPending}
            onClick={onReindex}
            type="button"
            variant="ghost"
            size="icon"
            className="h-7 w-7"
          >
            {reindexIsPending ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <RefreshCw className="h-3 w-3" />
            )}
          </Button>
        </div>
      </div>

      {hasError || reindexNotice ? (
        <div className="grid gap-1">
          {sourcesError ? <Notice title="Sources failed" tone="danger">{sourcesError}</Notice> : null}
          {reindexError ? <Notice title="Reindex failed" tone="danger">{reindexError}</Notice> : null}
          {reindexNotice ? <Notice title="Reindexed">{reindexNotice}</Notice> : null}
          {integrityError ? <Notice title="Integrity failed" tone="danger">{integrityError}</Notice> : null}
        </div>
      ) : null}
    </>
  );
}
