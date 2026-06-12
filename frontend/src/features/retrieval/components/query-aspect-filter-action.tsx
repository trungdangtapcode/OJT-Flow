import { CheckCircle2, ListFilter, Loader2 } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type {
  QueryAspectFilterApplyHandler,
  QueryAspectFilterEntryView,
} from "./query-aspect-plan-types";

export function QueryAspectFilterAction({
  aspectId,
  entry,
  isSearchPending,
  onApplyFilter,
}: {
  aspectId: string;
  entry: QueryAspectFilterEntryView;
  isSearchPending: boolean;
  onApplyFilter: QueryAspectFilterApplyHandler;
}) {
  if (!entry.supported) {
    return (
      <Badge key={`${aspectId}-${entry.field}-${entry.value}-unsupported`} variant="warning">
        unsupported {humanize(entry.field)}
      </Badge>
    );
  }

  return (
    <Button
      disabled={isSearchPending || entry.applied}
      key={`${aspectId}-${entry.field}-${entry.value}-apply`}
      onClick={() =>
        onApplyFilter({
          applied: false,
          confidence: 1,
          field: entry.field,
          reason: `Suggested by search aspect ${aspectId}.`,
          value: entry.value,
        })
      }
      size="sm"
      title={`Apply ${entry.label}=${entry.displayValue}`}
      type="button"
      variant={entry.applied ? "secondary" : "outline"}
    >
      {entry.applied ? (
        <CheckCircle2 className="h-4 w-4" />
      ) : isSearchPending ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <ListFilter className="h-4 w-4" />
      )}
      {entry.applied ? `${entry.label} applied` : `Apply ${entry.label}`}
    </Button>
  );
}
