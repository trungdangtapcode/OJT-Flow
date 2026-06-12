import { Search } from "lucide-react";

import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { RetrievalSource } from "../../../types";
import { formatCount } from "../model/retrieval-format";

export function SourceCard({
  onUseSource,
  source,
}: {
  onUseSource: (sourceId: string) => void;
  source: RetrievalSource;
}) {
  return (
    <article className="grid gap-2 rounded-md border border-border bg-muted/20 p-3 text-sm">
      <div className="min-w-0">
        <div className="break-words font-bold">{source.title}</div>
        <div className="break-all font-mono text-xs text-muted-foreground">
          {source.source_id}
        </div>
      </div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
          {humanize(source.source_type)}
        </span>
        {source.clinical_domain ? (
          <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
            {humanize(source.clinical_domain)}
          </span>
        ) : null}
        {source.standard_system ? (
          <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
            {source.standard_system}
          </span>
        ) : null}
        <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
          {formatCount(source.chunk_count, "chunk")}
        </span>
        {source.corpus_partition_label || source.corpus_partition_id ? (
          <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
            {source.corpus_partition_label ?? humanize(source.corpus_partition_id ?? "")}
          </span>
        ) : null}
        {source.corpus_visibility ? (
          <span className="rounded-full bg-card px-2 py-1 text-xs font-bold text-muted-foreground">
            {humanize(source.corpus_visibility)}
          </span>
        ) : null}
        {source.external_provider_allowed === false ? (
          <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-bold text-amber-800">
            No external provider
          </span>
        ) : null}
        {source.phi_allowed ? (
          <span className="rounded-full bg-rose-50 px-2 py-1 text-xs font-bold text-rose-800">
            PHI allowed
          </span>
        ) : null}
      </div>
      {source.retention_policy_id ? (
        <div className="break-words text-xs text-muted-foreground">
          Retention: {humanize(source.retention_policy_id)}
        </div>
      ) : null}
      <Button
        className="w-fit"
        onClick={() => onUseSource(source.source_id)}
        size="sm"
        type="button"
        variant="outline"
      >
        <Search className="h-4 w-4" />
        Use source
      </Button>
    </article>
  );
}
