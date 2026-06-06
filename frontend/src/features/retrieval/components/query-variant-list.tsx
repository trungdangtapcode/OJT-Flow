import { useEffect, useState } from "react";
import { CheckCircle2, Clipboard } from "lucide-react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { humanize } from "../../../lib/utils";
import type { RetrievalQueryVariant } from "../../../types";
import { SectionHelpText } from "./section-help-text";
import { TokenList } from "./token-list";

export function QueryVariantList({ variants }: { variants: RetrievalQueryVariant[] }) {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    if (!copiedKey) return undefined;
    const timeoutId = window.setTimeout(() => setCopiedKey(null), 1800);
    return () => window.clearTimeout(timeoutId);
  }, [copiedKey]);

  const copyVariant = async (variantKey: string, query: string) => {
    await copyTextToClipboard(query);
    setCopiedKey(variantKey);
  };

  if (!variants.length) {
    return (
      <TokenList
        description="No query rewrite variants were generated for this search."
        items={[]}
        title="Query rewrites"
      />
    );
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Query rewrites
      </div>
      <SectionHelpText>
        Query rewrites are backend-generated search variants. They improve recall but do not change the submitted payload. Copy a rewrite to rerun it manually or compare it with the submitted query.
      </SectionHelpText>
      <div className="grid gap-2">
        {variants.map((variant, index) => (
          <VariantRow
            isCopied={copiedKey === `${variant.source}-${variant.variant}-${index}`}
            key={`${variant.source}-${variant.variant}-${index}`}
            onCopy={() =>
              void copyVariant(`${variant.source}-${variant.variant}-${index}`, variant.variant)
            }
            variant={variant}
          />
        ))}
      </div>
    </div>
  );
}

function VariantRow({
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

async function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const element = document.createElement("textarea");
  element.value = text;
  element.setAttribute("readonly", "true");
  element.style.position = "fixed";
  element.style.left = "-9999px";
  document.body.appendChild(element);
  element.select();
  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(element);
  }
}
