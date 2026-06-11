import { QueryDiagnosticRow } from "./query-diagnostic-row";
export type { QueryDiagnosticListItem } from "./query-diagnostic-types";
import type { QueryDiagnosticListItem } from "./query-diagnostic-types";
import { SectionHelpText } from "./section-help-text";
import { TokenList } from "./token-list";

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
          <QueryDiagnosticRow diagnostic={diagnostic} key={diagnostic.code} />
        ))}
      </div>
    </div>
  );
}
