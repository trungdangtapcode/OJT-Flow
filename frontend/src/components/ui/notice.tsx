import { AlertCircle, Inbox } from "lucide-react";
import type * as React from "react";

import { cn } from "../../lib/utils";

export function Notice({
  title,
  children,
  tone = "neutral",
}: {
  title: string;
  children?: React.ReactNode;
  tone?: "neutral" | "danger";
}) {
  const Icon = tone === "danger" ? AlertCircle : Inbox;
  return (
    <div
      className={cn(
        "flex items-start gap-3.5 rounded-xl border p-5 text-sm",
        tone === "danger"
          ? "border-red-200/80 bg-red-50/80 text-red-800"
          : "border-border/50 bg-muted/30 text-muted-foreground",
      )}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
          tone === "danger" ? "bg-red-100 text-red-600" : "bg-primary/10 text-primary",
        )}
      >
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 pt-1">
        <div className={cn("font-semibold", tone === "danger" ? "text-red-900" : "text-foreground")}>
          {title}
        </div>
        {children ? <div className="mt-1.5 leading-relaxed">{children}</div> : null}
      </div>
    </div>
  );
}
