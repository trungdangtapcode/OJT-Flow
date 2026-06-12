import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import { correctiveActionTypeCountEntries } from "../model/corrective-actions";

export function CorrectiveActionTypeCountChips({
  counts,
}: {
  counts: Record<string, number>;
}) {
  const entries = correctiveActionTypeCountEntries(counts);
  if (!entries.length) return null;
  return (
    <>
      {entries.slice(0, 4).map(([actionType, count]) => (
        <Badge key={actionType} variant="muted">
          {humanize(actionType)} {count}
        </Badge>
      ))}
      {entries.length > 4 ? (
        <Badge variant="muted">+{entries.length - 4} action types</Badge>
      ) : null}
    </>
  );
}
