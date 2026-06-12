import { Badge } from "../../../components/ui/badge";
import { HelpTooltip } from "../../../components/ui/help-tooltip";

export function CockpitMetricCard({
  helpText,
  label,
  supporting,
  tone,
  value,
}: {
  helpText: string;
  label: string;
  supporting: string;
  tone: "success" | "warning" | "info";
  value: string;
}) {
  return (
    <div className="grid min-w-0 gap-1 rounded-md border border-border bg-card px-3 py-2">
      <span className="inline-flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
        {label}
        <HelpTooltip label={`${label} help`}>{helpText}</HelpTooltip>
      </span>
      <Badge variant={tone === "info" ? "default" : tone}>{value}</Badge>
      <span className="break-words text-xs leading-5 text-muted-foreground">
        {supporting}
      </span>
    </div>
  );
}
