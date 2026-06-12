import { Loader2, RefreshCw } from "lucide-react";

import { PageHeader } from "../../../components/layout/page-header";
import { Button } from "../../../components/ui/button";
import { Notice } from "../../../components/ui/notice";
import {
  RetrievalSummaryStrip,
  type RetrievalSummaryStripViewModel,
} from "./retrieval-summary-strip";
import { RetrievalInlineGuide } from "./retrieval-inline-guide";

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
  return (
    <>
      <PageHeader
        action={
          <Button
            disabled={reindexIsPending}
            onClick={onReindex}
            type="button"
            variant="outline"
          >
            {reindexIsPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Reindex
          </Button>
        }
        title="Retrieval"
        description="Inspect trusted healthcare search, rank signals, source filters, and graph handoff."
      />

      <RetrievalSummaryStrip summary={summary} />

      <RetrievalInlineGuide />

      {sourcesError ? (
        <Notice title="Retrieval sources could not be loaded" tone="danger">
          {sourcesError}
        </Notice>
      ) : null}
      {reindexError ? (
        <Notice title="Retrieval index could not be refreshed" tone="danger">
          {reindexError}
        </Notice>
      ) : null}
      {reindexNotice ? (
        <Notice title="Retrieval index refreshed">{reindexNotice}</Notice>
      ) : null}
      {integrityError ? (
        <Notice title="Retrieval integrity could not be checked" tone="danger">
          {integrityError}
        </Notice>
      ) : null}
    </>
  );
}
