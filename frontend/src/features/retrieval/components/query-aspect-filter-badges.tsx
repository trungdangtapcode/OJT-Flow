import { Badge } from "../../../components/ui/badge";
import type { QueryAspectFilterEntryView } from "./query-aspect-plan-types";

export function QueryAspectFilterBadges({
  aspectId,
  entries,
}: {
  aspectId: string;
  entries: QueryAspectFilterEntryView[];
}) {
  if (!entries.length) {
    return null;
  }

  return (
    <div className="flex min-w-0 flex-wrap gap-1">
      {entries.map((entry) => (
        <Badge
          key={`${aspectId}-${entry.field}`}
          variant={entry.applied ? "success" : "muted"}
        >
          {entry.label}={entry.displayValue}
        </Badge>
      ))}
    </div>
  );
}
