import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalSource } from "../../../types";
import { formatSourceCount } from "./source-scope-picker-format";

export function SourceMetadataBadges({ source }: { source: RetrievalSource }) {
  return (
    <span className="flex min-w-0 flex-wrap gap-1.5">
      <Badge variant="muted">{humanize(source.source_type)}</Badge>
      {source.clinical_domain ? (
        <Badge variant="muted">{humanize(source.clinical_domain)}</Badge>
      ) : null}
      {source.standard_system ? (
        <Badge variant="muted">{source.standard_system}</Badge>
      ) : null}
      <Badge variant="muted">{formatSourceCount(source.chunk_count, "chunk")}</Badge>
    </span>
  );
}
