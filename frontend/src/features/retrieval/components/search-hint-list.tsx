import {
  copyTextToClipboard,
  useCopyFeedback,
} from "./copy-feedback";
import { SearchHintCard } from "./search-hint-card";
import type { SearchHintStack } from "./search-plan-detail-panels";
import { TokenList } from "./token-list";

export function SearchHintList({ hints }: { hints: SearchHintStack[] }) {
  const { copiedKey, markCopied } = useCopyFeedback();

  const copyHintQuery = async (hintKey: string, query: string) => {
    await copyTextToClipboard(query);
    markCopied(hintKey);
  };

  if (!hints.length) {
    return <TokenList items={[]} title="Medical search hints" />;
  }
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">
        Medical search hints
      </div>
      <div className="grid gap-2">
        {hints.map((hint) => {
          const hintKey = `${hint.target}-${hint.query}`;
          return (
            <SearchHintCard
              copied={copiedKey === hintKey}
              hint={hint}
              hintKey={hintKey}
              key={hintKey}
              onCopy={(key, query) => void copyHintQuery(key, query)}
            />
          );
        })}
      </div>
    </div>
  );
}
