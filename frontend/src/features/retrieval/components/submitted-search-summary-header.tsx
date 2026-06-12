import { RefreshCw } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";

export function SubmittedSearchSummaryHeader({
  isRestoreDisabled,
  isStale,
  onRestore,
}: {
  isRestoreDisabled: boolean;
  isStale: boolean;
  onRestore: () => void;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
      <div className="text-xs font-bold uppercase text-muted-foreground">Submitted search</div>
      <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
        <Badge variant={isStale ? "warning" : "success"}>
          {isStale ? "displayed request" : "current request"}
        </Badge>
        {isStale ? (
          <Button
            disabled={isRestoreDisabled}
            onClick={onRestore}
            size="sm"
            title="Restore submitted search"
            type="button"
            variant="outline"
          >
            <RefreshCw className="h-4 w-4" />
            Restore
          </Button>
        ) : null}
      </div>
    </div>
  );
}
