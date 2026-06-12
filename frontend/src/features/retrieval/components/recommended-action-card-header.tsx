import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalRecommendedAction } from "../../../types";
import { qualitySignalBadgeVariant } from "./quality-signal-list";

export function RecommendedActionCardHeader({
  action,
  sourceLabel,
}: {
  action: RetrievalRecommendedAction;
  sourceLabel: string | null;
}) {
  return (
    <div className="min-w-0">
      <div className="flex min-w-0 flex-wrap items-center gap-1.5">
        <Badge variant={qualitySignalBadgeVariant(action.severity)}>P{action.priority}</Badge>
        <Badge variant="muted">{humanize(action.action_type)}</Badge>
        {sourceLabel ? <Badge variant="muted">{sourceLabel}</Badge> : null}
        {action.source_signal_codes.slice(0, 2).map((code) => (
          <Badge
            className="max-w-full break-words"
            key={`${action.action_id}-${code}`}
            variant="muted"
          >
            {humanize(code)}
          </Badge>
        ))}
      </div>
      <div className="mt-2 break-words text-sm font-black">{action.title}</div>
      <div className="mt-1 break-words text-xs leading-5 text-muted-foreground">
        {action.description}
      </div>
    </div>
  );
}
