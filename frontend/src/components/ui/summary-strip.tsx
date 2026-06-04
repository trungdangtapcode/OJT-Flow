import * as React from "react";

import { Skeleton } from "./skeleton";
import { cn } from "../../lib/utils";

type SummaryTone = "default" | "success" | "warning" | "info" | "neutral";

const columnClasses: Record<3 | 4 | 5, string> = {
  3: "grid-cols-1 sm:grid-cols-3",
  4: "grid-cols-2 xl:grid-cols-4",
  5: "grid-cols-1 lg:grid-cols-5",
};

const toneClasses: Record<SummaryTone, string> = {
  default: "bg-emerald-50 text-emerald-700",
  success: "bg-emerald-50 text-emerald-700",
  warning: "bg-amber-50 text-amber-700",
  info: "bg-blue-50 text-blue-700",
  neutral: "bg-slate-100 text-slate-700",
};

export function SummaryStrip({
  children,
  className,
  columns = 4,
}: {
  children: React.ReactNode;
  className?: string;
  columns?: 3 | 4 | 5;
}) {
  return (
    <section
      className={cn(
        "min-w-0 overflow-hidden rounded-lg border border-border bg-border shadow-[0_1px_3px_rgba(16,24,40,0.05)]",
        className,
      )}
    >
      <div className={cn("grid min-w-0 gap-px", columnClasses[columns])}>
        {children}
      </div>
    </section>
  );
}

export function SummaryStripItem({
  icon: Icon,
  label,
  loading = false,
  supporting,
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
    <div className="grid min-w-0 grid-cols-[minmax(0,1fr)_auto] gap-2 bg-card p-3 sm:gap-3 sm:p-4">
      <div className="min-w-0">
        <div className="line-clamp-2 break-normal text-[11px] font-bold uppercase leading-tight text-muted-foreground">
          {label}
        </div>
        <div
          className="mt-1 min-w-0 break-words text-base font-black leading-tight tabular-nums sm:text-2xl"
          data-summary-label={label}
          data-testid="summary-strip-value"
        >
          {loading ? (
            <>
              <Skeleton
                aria-label={`Loading ${label}`}
                className="h-7 w-20"
                role="status"
              />
              <span className="sr-only">Loading {label}</span>
            </>
          ) : (
            value
          )}
        </div>
        <div className="mt-1 hidden line-clamp-1 text-[11px] leading-4 text-muted-foreground min-[520px]:block sm:text-xs">
          {supporting}
        </div>
      </div>
      <span className={cn("self-start shrink-0 rounded-md p-1.5", toneClasses[tone])}>
        <Icon className="h-3.5 w-3.5" />
      </span>
    </div>
  );
}
