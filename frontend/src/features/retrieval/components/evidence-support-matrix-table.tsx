import { Table, TBody, TH, THead, TR } from "../../../components/ui/table";
import { EvidenceSupportMatrixTableRow } from "./evidence-support-matrix-table-row";
import type {
  EvidenceSupportMatrixFormatters,
  EvidenceSupportMatrixRowView,
} from "./evidence-support-matrix-types";

export function EvidenceSupportMatrixTable({
  formatScore,
  humanize,
  judgmentBadgeVariant,
  judgmentLabel,
  rows,
  supportStatusBadgeVariant,
}: EvidenceSupportMatrixFormatters & {
  rows: EvidenceSupportMatrixRowView[];
}) {
  return (
    <div className="hidden overflow-auto rounded-md border border-border bg-card md:block">
      <Table>
        <THead>
          <TR>
            <TH>Rank</TH>
            <TH>Source</TH>
            <TH>Standard</TH>
            <TH>Evidence buckets</TH>
            <TH>Support</TH>
            <TH>Judgment</TH>
            <TH>Score</TH>
          </TR>
        </THead>
        <TBody>
          {rows.map((row) => (
            <EvidenceSupportMatrixTableRow
              formatScore={formatScore}
              humanize={humanize}
              judgmentBadgeVariant={judgmentBadgeVariant}
              judgmentLabel={judgmentLabel}
              key={row.evidenceId}
              row={row}
              supportStatusBadgeVariant={supportStatusBadgeVariant}
            />
          ))}
        </TBody>
      </Table>
    </div>
  );
}
