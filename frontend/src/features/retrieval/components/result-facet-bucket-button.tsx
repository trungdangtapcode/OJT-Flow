import { ListFilter, Loader2 } from "lucide-react";

import { cn } from "../../../lib/utils";
import type { RetrievalFacetBucket } from "../../../types";
import type { ResultFacetFilterField } from "./result-facet-types";

export function ResultFacetBucketButton({
  applied,
  bucket,
  field,
  formatter,
  isSearchPending,
  label,
  onApplyFacet,
}: {
  applied: boolean;
  bucket: RetrievalFacetBucket;
  field: ResultFacetFilterField;
  formatter: (value: string) => string;
  isSearchPending: boolean;
  label: string;
  onApplyFacet: (field: ResultFacetFilterField, value: string) => void;
}) {
  const displayValue = formatter(bucket.value);
  return (
    <button
      aria-label={`Filter by ${label} ${displayValue}`}
      aria-pressed={applied}
      className={cn(
        "inline-flex max-w-full items-center gap-1.5 rounded-full border px-2 py-1 text-xs font-bold transition-colors focus-ring disabled:cursor-not-allowed disabled:opacity-70",
        applied
          ? "border-emerald-200 bg-emerald-100 text-emerald-900"
          : "border-border bg-card text-muted-foreground hover:border-primary/40 hover:bg-primary/10 hover:text-foreground",
      )}
      disabled={applied || isSearchPending}
      onClick={() => onApplyFacet(field, bucket.value)}
      title={applied ? `${displayValue} is already applied` : `Apply ${label}=${displayValue}`}
      type="button"
    >
      {isSearchPending && !applied ? (
        <Loader2 className="h-3 w-3 animate-spin" />
      ) : (
        <ListFilter className="h-3 w-3" />
      )}
      <span className="break-words">{displayValue}</span>
      <span className="tabular-nums text-foreground">{bucket.count}</span>
      {applied ? <span>applied</span> : null}
    </button>
  );
}
