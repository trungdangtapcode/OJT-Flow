import { cn } from "../../../lib/utils";

export function sourceFilterChipClass(active: boolean) {
  return cn(
    "rounded-full border px-2.5 py-1 text-xs font-bold transition-colors",
    active
      ? "border-primary bg-primary/10 text-primary"
      : "border-border bg-background text-muted-foreground hover:bg-muted",
  );
}
