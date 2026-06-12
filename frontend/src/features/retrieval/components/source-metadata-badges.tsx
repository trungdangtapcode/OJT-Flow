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
      {source.corpus_partition_label || source.corpus_partition_id ? (
        <Badge variant="muted">
          {source.corpus_partition_label ?? humanize(source.corpus_partition_id ?? "")}
        </Badge>
      ) : null}
      {source.corpus_visibility ? (
        <Badge variant="muted">{humanize(source.corpus_visibility)}</Badge>
      ) : null}
      {source.external_provider_allowed === false ? (
        <Badge variant="warning">No external provider</Badge>
      ) : null}
      {source.phi_allowed ? <Badge variant="destructive">PHI allowed</Badge> : null}
    </span>
  );
}
