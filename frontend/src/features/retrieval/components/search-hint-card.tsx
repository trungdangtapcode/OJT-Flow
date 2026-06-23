import { CheckCircle2, Clipboard, ExternalLink } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { SearchHintStack } from "./search-plan-detail-panels";
import { SearchHintMetadata } from "./search-hint-metadata-details";
import { TokenList } from "./token-list";

export function SearchHintCard({
  copied,
  hint,
  hintKey,
  onCopy,
}: {
  copied: boolean;
  hint: SearchHintStack;
  hintKey: string;
  onCopy: (hintKey: string, query: string) => void;
}) {
  return (
    <div
      className="grid gap-1.5 rounded-lg border border-border/60 bg-card p-2 text-xs"
      key={hintKey}
    >
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <span className="break-words font-bold">{humanize(hint.target)}</span>
        <div className="flex min-w-0 flex-wrap justify-end gap-1.5">
          <Badge variant={hint.url ? "success" : "muted"}>
            {hint.url ? "launchable hint" : "syntax hint"}
          </Badge>
          <Button
            onClick={() => onCopy(hintKey, hint.query)}
            size="sm"
            title="Copy medical search hint"
            type="button"
            variant="outline"
          >
            {copied ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <Clipboard className="h-4 w-4" />
            )}
            {copied ? "Copied" : "Copy"}
          </Button>
          {hint.url ? (
            <Button asChild size="sm" title="Open medical search hint" variant="outline">
              <a href={hint.url} rel="noopener noreferrer" target="_blank">
                <ExternalLink className="h-4 w-4" />
                Open
              </a>
            </Button>
          ) : null}
        </div>
      </div>
      <code className="block max-h-24 overflow-auto break-words rounded bg-muted px-2 py-1 font-mono text-xs">
        {hint.query}
      </code>
      <SearchHintMetadata metadata={hint.metadata} />
      <div className="break-words text-muted-foreground">{hint.rationale}</div>
      {hint.warnings.length ? (
        <TokenList items={hint.warnings} title="Hint warnings" tone="warning" />
      ) : null}
    </div>
  );
}
