import * as React from "react";

import { cn } from "../../lib/utils";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

const variants: Record<BadgeVariant, string> = {
  default: "bg-slate-100 text-slate-700",
  success: "bg-emerald-50 text-emerald-700 border-emerald-200/60",
  warning: "bg-amber-50 text-amber-700 border-amber-200/60",
  destructive: "bg-red-50 text-red-700 border-red-200/60",
  muted: "bg-muted/70 text-muted-foreground border-border/50",
};

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        "inline-flex w-fit max-w-full min-w-0 items-center rounded-lg border px-2.5 py-0.5 text-left text-xs font-semibold leading-tight whitespace-normal break-words",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
