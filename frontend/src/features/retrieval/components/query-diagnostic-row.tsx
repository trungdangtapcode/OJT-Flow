import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import { queryDiagnosticMetadataChips } from "./query-diagnostic-metadata";
import type { BadgeVariant, QueryDiagnosticListItem } from "./query-diagnostic-types";

export function QueryDiagnosticRow({
  diagnostic,
}: {
  diagnostic: QueryDiagnosticListItem;
}) {
  return (
    <div className="grid gap-1 rounded-lg border border-border/60 bg-card p-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="break-words font-bold">{humanize(diagnostic.code)}</span>
        <Badge variant={diagnosticBadgeVariant(diagnostic.severity)}>
          {humanize(diagnostic.severity)}
        </Badge>
      </div>
      <div className="break-words text-muted-foreground">{diagnostic.message}</div>
      <DiagnosticMetadataChips metadata={diagnostic.metadata} />
      <div className="break-words font-semibold text-foreground">
        {diagnostic.suggestedAction}
      </div>
    </div>
  );
}

function DiagnosticMetadataChips({ metadata }: { metadata: Record<string, unknown> }) {
  const chips = queryDiagnosticMetadataChips(metadata);
  if (!chips.length) return null;
  return (
    <div className="flex min-w-0 flex-wrap gap-1">
      {chips.map((chip) => (
        <Badge className="max-w-full break-words" key={chip} variant="muted">
          {chip}
        </Badge>
      ))}
    </div>
  );
}

function diagnosticBadgeVariant(severity: string): BadgeVariant {
  if (severity === "warning") return "warning";
  if (severity === "error") return "destructive";
  if (severity === "info") return "muted";
  return "default";
}
