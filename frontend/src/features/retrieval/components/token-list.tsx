import { cn } from "../../../lib/utils";
import { SectionHelpText } from "./section-help-text";

export function TokenList({
  description,
  items,
  title,
  tone = "neutral",
}: {
  description?: string;
  items: string[];
  title: string;
  tone?: "neutral" | "warning";
}) {
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold uppercase text-muted-foreground">{title}</div>
      {description ? <SectionHelpText>{description}</SectionHelpText> : null}
      <div className="flex min-w-0 flex-wrap gap-1.5">
        {items.map((item) => (
          <span
            className={cn(
              "max-w-full break-words rounded-full px-2 py-1 text-xs font-bold",
              tone === "warning"
                ? "bg-amber-100 text-amber-900"
                : "bg-muted text-muted-foreground",
            )}
            key={item}
          >
            {item}
          </span>
        ))}
        {!items.length ? (
          <span className="text-xs font-semibold text-muted-foreground">none</span>
        ) : null}
      </div>
    </div>
  );
}
