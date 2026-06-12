import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalSearchPayload } from "../../../types";

export function SubmittedSearchMetadataChips({ payload }: { payload: RetrievalSearchPayload }) {
  return (
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
  );
}
