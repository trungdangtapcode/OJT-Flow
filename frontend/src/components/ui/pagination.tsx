import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "./button";

export function PaginationFooter({
  page,
  pageSize,
  total,
  onPrevious,
  onNext,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPrevious: () => void;
  onNext: () => void;
}) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const displayPage = Math.min(page, pageCount);
  const firstItem = total === 0 ? 0 : (displayPage - 1) * pageSize + 1;
  const lastItem = Math.min(displayPage * pageSize, total);
  const hasNextPage = displayPage * pageSize < total;
  return (
    <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-border/40 bg-muted/20 px-4 py-2.5 text-sm text-muted-foreground">
      <span className="tabular-nums">
        {firstItem}–{lastItem} of {total}
      </span>
      <div className="flex items-center gap-1">
        <Button disabled={displayPage <= 1} onClick={onPrevious} size="sm" type="button" variant="ghost">
          <ChevronLeft className="h-4 w-4" />
          Prev
        </Button>
        <span className="px-2 text-xs font-medium tabular-nums">
          {displayPage} / {pageCount}
        </span>
        <Button disabled={!hasNextPage} onClick={onNext} size="sm" type="button" variant="ghost">
          Next
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
