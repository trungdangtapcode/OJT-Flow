import type { RetrievalQueryVariant } from "../../../types";
import {
  copyTextToClipboard,
  useCopyFeedback,
} from "./copy-feedback";
import { QueryVariantRow } from "./query-variant-row";
import { SectionHelpText } from "./section-help-text";
import { TokenList } from "./token-list";

export function QueryVariantList({ variants }: { variants: RetrievalQueryVariant[] }) {
  const { copiedKey, markCopied } = useCopyFeedback();

  const copyVariant = async (variantKey: string, query: string) => {
    await copyTextToClipboard(query);
    markCopied(variantKey);
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
          <QueryVariantRow
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
