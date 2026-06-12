import {
  Card,
  CardContent,
} from "../../../components/ui/card";
import { IntegrityLoadingNotice } from "./integrity-loading-notice";
import { IntegrityPanelHeader } from "./integrity-panel-header";
import type { IntegrityPanelProps } from "./integrity-panel-types";
import { IntegritySourceChecks } from "./integrity-source-checks";
import { IntegritySummaryMetrics } from "./integrity-summary-metrics";
import { IntegrityWarnings } from "./integrity-warnings";

export function IntegrityPanel({
  checks,
  formatCount,
  formatHash,
  includeCorpus,
  integrityBadgeVariant,
  isFetching,
  onRefresh,
  onToggleCorpus,
  report,
}: IntegrityPanelProps) {
  return (
    <Card className="min-w-0 overflow-hidden">
      <IntegrityPanelHeader
        includeCorpus={includeCorpus}
        isFetching={isFetching}
        onRefresh={onRefresh}
        onToggleCorpus={onToggleCorpus}
        report={report}
      />
      <CardContent className="grid gap-4 pt-4">
        {!report ? (
          <IntegrityLoadingNotice />
        ) : (
          <>
            <IntegritySummaryMetrics
              integrityBadgeVariant={integrityBadgeVariant}
              report={report}
            />
            <IntegrityWarnings report={report} />
            <IntegritySourceChecks
              checks={checks}
              formatCount={formatCount}
              formatHash={formatHash}
              integrityBadgeVariant={integrityBadgeVariant}
              report={report}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
