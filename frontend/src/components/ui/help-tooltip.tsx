import * as React from "react";
import { HelpCircle } from "lucide-react";

import { cn } from "../../lib/utils";

export function HelpTooltip({
  children,
  className,
  label,
}: {
  children: React.ReactNode;
  className?: string;
  label: string;
}) {
  return (
    <span className={cn("group/help relative inline-flex align-middle", className)}>
      <span
        aria-label="Show help"
        className="inline-flex h-5 w-5 cursor-help items-center justify-center rounded-full text-muted-foreground focus-ring hover:text-foreground"
        role="button"
        tabIndex={0}
        title={label}
      >
        <HelpCircle className="h-3.5 w-3.5" />
      </span>
      <span
        className="pointer-events-none absolute left-1/2 top-6 z-30 hidden w-72 -translate-x-1/2 rounded-md border border-border bg-card p-3 text-left text-xs font-semibold leading-5 text-card-foreground shadow-lg group-hover/help:block group-focus-within/help:block"
        role="tooltip"
      >
        {children}
      </span>
    </span>
  );
}
