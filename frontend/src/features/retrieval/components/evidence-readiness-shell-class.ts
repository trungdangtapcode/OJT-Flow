import { cn } from "../../../lib/utils";

export function evidenceReadinessShellClass(ready: boolean) {
  return cn(
    "grid gap-3 rounded-md border p-3",
    ready
      ? "border-emerald-200 bg-emerald-50"
      : "border-amber-200 bg-amber-50",
  );
}
