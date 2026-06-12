import { Badge } from "../../../components/ui/badge";
import type { SearchHintParameterExample } from "./search-hint-metadata";

export function SearchHintParameterExamplesSection({
  examples,
}: {
  examples: SearchHintParameterExample[];
}) {
  if (!examples.length) return null;
  return (
    <div className="grid gap-1.5">
      <div className="font-black uppercase text-muted-foreground">Parameter examples</div>
      {examples.map((example) => (
        <div
          className="grid gap-1 rounded-md border border-border bg-card px-2 py-1.5"
          key={`${example.name}:${example.example}`}
        >
          <div className="flex min-w-0 flex-wrap items-center gap-1.5">
            <Badge variant={example.matchedDatasetField ? "success" : "muted"}>
              {example.name}
            </Badge>
            <span className="break-words text-muted-foreground">{example.targetField}</span>
          </div>
          <code className="break-words font-mono text-[11px]">{example.example}</code>
        </div>
      ))}
    </div>
  );
}
