import type { RetrievalIntegrityReport } from "../../../types";
import { TokenList } from "./token-list";

export function IntegrityWarnings({ report }: { report: RetrievalIntegrityReport }) {
  return report.warnings.length ? (
    <TokenList items={report.warnings} title="Integrity warnings" tone="warning" />
  ) : (
    <TokenList items={[]} title="Integrity warnings" />
  );
}
