import { Fragment } from "react";

import { highlightedParts } from "./evidence-highlight-utils";

export function HighlightedText({ text, terms }: { text: string; terms: string[] }) {
  const parts = highlightedParts(text, terms);
  return (
    <>
      {parts.map((part, index) =>
        part.highlight ? (
          <mark
            className="rounded bg-amber-100 px-0.5 font-bold text-amber-950"
            key={`${part.text}-${index}`}
          >
            {part.text}
          </mark>
        ) : (
          <Fragment key={`${part.text}-${index}`}>{part.text}</Fragment>
        ),
      )}
    </>
  );
}
