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
    <div className="mt-3 flex items-center justify-between gap-3 text-sm text-muted-foreground">
      <span>
        Showing {firstItem}-{lastItem} of {total} · Page {displayPage} / {pageCount}
      </span>
      <div className="flex gap-2">
        <Button disabled={displayPage <= 1} onClick={onPrevious} size="sm" type="button" variant="outline">
          Previous
        </Button>
        <Button disabled={!hasNextPage} onClick={onNext} size="sm" type="button" variant="outline">
          Next
        </Button>
      </div>
    </div>
  );
}
