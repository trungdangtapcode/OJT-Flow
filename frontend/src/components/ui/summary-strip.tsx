import * as React from "react";

import { Skeleton } from "./skeleton";
import { cn } from "../../lib/utils";

type SummaryTone = "default" | "success" | "warning" | "info" | "neutral";

const toneDot: Record<SummaryTone, string> = {
  default: "bg-teal-500",
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  info: "bg-blue-500",
  neutral: "bg-slate-400",
};

export function SummaryStrip({
  children,
  className,
  columns: _columns = 4,
}: {
  children: React.ReactNode;
  className?: string;
  columns?: 3 | 4 | 5;
}) {
  return (
    <section
      className={cn(
        "flex min-w-0 flex-wrap items-center gap-2",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function SummaryStripItem({
  icon: _Icon,
  label,
  loading = false,
  supporting: _supporting,
  tone = "default",
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  loading?: boolean;
  supporting: React.ReactNode;
  tone?: SummaryTone;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-1.5 rounded-full border border-border/50 bg-card px-3 py-1.5 text-xs font-semibold shadow-sm">
      <span className={cn("h-2 w-2 shrink-0 rounded-full", toneDot[tone])} />
      <span className="text-muted-foreground">{label}</span>
      <span className="font-bold text-foreground">
        {loading ? (
          <Skeleton
            aria-label={`Loading ${label}`}
            className="inline-block h-3.5 w-10"
            role="status"
          />
        ) : (
          value
        )}
      </span>
    </div>
  );
}
