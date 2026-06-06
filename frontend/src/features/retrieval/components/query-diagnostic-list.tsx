import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import { SectionHelpText } from "./section-help-text";
import { TokenList } from "./token-list";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export type QueryDiagnosticListItem = {
  code: string;
  metadata: Record<string, unknown>;
  message: string;
  severity: string;
  suggestedAction: string;
};

export function QueryDiagnosticList({
  diagnostics,
}: {
  diagnostics: QueryDiagnosticListItem[];
}) {
  if (!diagnostics.length) {
    return (
      <TokenList
        description="No query diagnostic warnings were emitted."
        items={[]}
        title="Query diagnostics"
      />
    );
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Query diagnostics
      </div>
      <SectionHelpText>
        Query diagnostics explain parser, expansion, and safety issues detected before ranking.
      </SectionHelpText>
      <div className="grid gap-2">
        {diagnostics.map((diagnostic) => (
          <div
            className="grid gap-1 rounded-md border border-border bg-card p-2 text-xs"
            key={diagnostic.code}
          >
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
        ))}
      </div>
    </div>
  );
}

function DiagnosticMetadataChips({ metadata }: { metadata: Record<string, unknown> }) {
  const activeFilters = stringArrayValue(metadata.active_metadata_filters);
  const suggestedStandards = stringArrayValue(metadata.suggested_standards);
  const appliedStandard = optionalStringValue(metadata.applied_standard);
  const tokenCount = numberValue(metadata.query_token_count);
  const filterCount = numberValue(metadata.active_metadata_filter_count);
  const chips = [
    tokenCount !== null ? `${tokenCount} query token${tokenCount === 1 ? "" : "s"}` : "",
    filterCount !== null ? `${filterCount} active filter${filterCount === 1 ? "" : "s"}` : "",
    appliedStandard ? `applied ${appliedStandard}` : "",
    suggestedStandards.length ? `suggested ${suggestedStandards.join(", ")}` : "",
    activeFilters.length ? `filters ${activeFilters.join(", ")}` : "",
  ].filter(Boolean);
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

function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

function optionalStringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
