import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalQueryVariant } from "../../../types";
import { formatSearchPlanDetailCount } from "./search-plan-detail-format";

export function SearchPlanRewritePreview({
  variants,
}: {
  variants: RetrievalQueryVariant[];
}) {
  if (!variants.length) return null;

  return (
    <details className="rounded-md border border-border bg-card">
      <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-2 px-3 py-2">
        <span className="text-xs font-black uppercase text-muted-foreground">
          Query rewrites
        </span>
        <Badge variant="muted">
          {formatSearchPlanDetailCount(variants.length, "variant")}
        </Badge>
      </summary>
      <div className="grid gap-2 border-t border-border p-3">
        {variants.slice(0, 6).map((variant, index) => (
          <div className="grid gap-1 text-xs" key={`${variant.source}-${variant.variant}-${index}`}>
            <div className="flex min-w-0 flex-wrap items-center gap-1.5">
              <Badge variant="muted">{humanize(variant.source)}</Badge>
              <span className="break-words font-semibold text-muted-foreground">
                {variant.reason}
              </span>
            </div>
            <code className="max-w-full break-words rounded bg-muted px-2 py-1 font-mono">
              {variant.variant}
            </code>
          </div>
        ))}
      </div>
    </details>
  );
}
