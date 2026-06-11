import { CheckCircle2, Clipboard } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { RetrievalQueryVariant } from "../../../types";

export function QueryVariantRow({
  isCopied,
  onCopy,
  variant,
}: {
  isCopied: boolean;
  onCopy: () => void;
  variant: RetrievalQueryVariant;
}) {
  return (
    <div className="grid gap-1 rounded-md border border-border bg-card p-2 text-xs">
      <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
        <code className="min-w-0 flex-1 break-words rounded bg-muted px-2 py-1 font-mono">
          {variant.variant}
        </code>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant="muted">{humanize(variant.source)}</Badge>
          <Button
            aria-label="Copy query rewrite"
            onClick={onCopy}
            size="sm"
            type="button"
            variant="outline"
          >
            {isCopied ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <Clipboard className="h-4 w-4" />
            )}
            {isCopied ? "Copied" : "Copy"}
          </Button>
        </div>
      </div>
      <div className="break-words font-semibold text-muted-foreground">
        {variant.reason}
      </div>
    </div>
  );
}
