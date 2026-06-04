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
        "flex items-start gap-3 rounded-md border p-4 text-sm",
        tone === "danger"
          ? "border-red-200 bg-red-50 text-red-900"
          : "border-border bg-muted/40 text-muted-foreground",
      )}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="min-w-0">
        <div className={cn("font-bold", tone === "danger" ? "text-red-950" : "text-foreground")}>
          {title}
        </div>
        {children ? <div className="mt-1">{children}</div> : null}
      </div>
    </div>
  );
}
