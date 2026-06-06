import { RefreshCw } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { RetrievalSearchPayload } from "../../../types";
import type { ActiveFilterBarEntry } from "./active-filter-bar";

export function SubmittedSearchSummary({
  filters,
  isRestoreDisabled,
  isStale,
  onRestore,
  payload,
}: {
  filters: ActiveFilterBarEntry[];
  isRestoreDisabled: boolean;
  isStale: boolean;
  onRestore: () => void;
  payload: RetrievalSearchPayload;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-bold uppercase text-muted-foreground">Submitted search</div>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={isStale ? "warning" : "success"}>
            {isStale ? "displayed request" : "current request"}
          </Badge>
          {isStale ? (
            <Button
              disabled={isRestoreDisabled}
              onClick={onRestore}
              size="sm"
              title="Restore submitted search"
              type="button"
              variant="outline"
            >
              <RefreshCw className="h-4 w-4" />
              Restore
            </Button>
          ) : null}
        </div>
      </div>
      <div className="grid gap-2 text-sm">
        <div className="break-words font-semibold">{payload.query}</div>
        <div className="flex min-w-0 flex-wrap gap-1.5">
          <Badge variant="muted">top {payload.top_k}</Badge>
          {payload.schema_id ? <Badge variant="muted">{payload.schema_id}</Badge> : null}
          {payload.detected_format ? (
            <Badge variant="muted">{humanize(payload.detected_format)}</Badge>
          ) : null}
          {payload.resource_type ? <Badge variant="muted">{payload.resource_type}</Badge> : null}
          {payload.fields.slice(0, 8).map((field) => (
            <span
              className="max-w-full break-words rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground"
              key={field}
            >
              {field}
            </span>
          ))}
          {payload.fields.length > 8 ? (
            <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
              +{payload.fields.length - 8} fields
            </span>
          ) : null}
        </div>
        {filters.length ? (
          <div className="flex min-w-0 flex-wrap gap-1.5">
            {filters.map((filter) => (
              <span
                className="max-w-full break-words rounded-full border border-primary/20 bg-primary/10 px-2 py-1 text-xs font-bold text-foreground"
                key={filter.field}
              >
                {filter.label}: {filter.displayValue}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
