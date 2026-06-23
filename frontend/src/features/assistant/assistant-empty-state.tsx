import { Sparkles } from "lucide-react";

import { Notice } from "../../components/ui/notice";
import type { AssistantExample } from "../../types";

export function ChatEmptyState({
  error,
  examples,
  isLoading,
  onSelect,
}: {
  error: string | null;
  examples: AssistantExample[];
  isLoading: boolean;
  onSelect: (example: AssistantExample) => void;
}) {
  return (
    <div className="mx-auto grid min-h-[420px] max-w-3xl place-items-center">
      <div className="grid w-full gap-5 text-center">
        <div>
          <div className="mx-auto grid h-12 w-12 place-items-center rounded-full border border-border bg-muted">
            <Sparkles className="h-6 w-6 text-primary" />
          </div>
          <div className="mt-3 text-xl font-black">Start with a healthcare data task</div>
          <div className="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
            The assistant will call backend tools, return evidence, and flag review gates.
          </div>
        </div>
        {error ? (
          <Notice title="Examples unavailable" tone="danger">
            {error}
          </Notice>
        ) : null}
        {!error && isLoading ? (
          <div className="grid gap-3 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <div
                aria-hidden="true"
                className="h-28 rounded-lg border border-border/60 bg-muted/35"
                key={index}
              />
            ))}
          </div>
        ) : null}
        {!error && !isLoading && examples.length ? (
          <div className="grid min-w-0 gap-3 text-left sm:grid-cols-3">
            {examples.map((example) => (
              <button
                className="grid min-h-28 min-w-0 gap-2 rounded-lg border border-border/60 bg-card p-3 text-left transition hover:border-primary hover:bg-primary/5"
                key={example.example_id}
                onClick={() => onSelect(example)}
                type="button"
              >
                <div className="min-w-0 break-words text-sm font-black">{example.label}</div>
                <div className="min-w-0 break-words text-sm leading-5 text-muted-foreground">
                  {example.description}
                </div>
              </button>
            ))}
          </div>
        ) : null}
        {!error && !isLoading && !examples.length ? (
          <div className="rounded-lg border border-border/60 bg-muted/25 p-3 text-sm text-muted-foreground">
            No starter tasks are configured.
          </div>
        ) : null}
      </div>
    </div>
  );
}
