import * as React from "react";

import { cn } from "../../lib/utils";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

const variants: Record<BadgeVariant, string> = {
  default: "border border-slate-200 bg-secondary text-secondary-foreground",
  success: "border border-emerald-200 bg-emerald-50 text-emerald-800",
  warning: "border border-amber-200 bg-warning text-warning-foreground",
  destructive: "border border-red-200 bg-red-50 text-red-800",
  muted: "border border-border bg-muted text-muted-foreground",
};

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        "inline-flex w-fit items-center rounded-full px-2.5 py-1 text-xs font-bold leading-none",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
