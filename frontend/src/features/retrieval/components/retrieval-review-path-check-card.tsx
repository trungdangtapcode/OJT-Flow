import {
  AlertTriangle,
  CheckCircle2,
  Database,
  FileSearch,
  ShieldCheck,
} from "lucide-react";

import { cn } from "../../../lib/utils";
import type { RetrievalReviewCheck } from "../model/retrieval-review-path";

const checkIcons: Record<RetrievalReviewCheck["code"], typeof CheckCircle2> = {
  readiness: ShieldCheck,
  required_support: Database,
  top_hit_support: FileSearch,
  warnings: AlertTriangle,
};

export function RetrievalReviewPathCheckCard({
  item,
}: {
  item: RetrievalReviewCheck;
}) {
  const Icon = checkIcons[item.code];
  return (
    <div className="grid min-w-0 gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 items-start gap-2">
        <Icon
          className={cn(
            "mt-0.5 h-4 w-4 shrink-0",
            item.status === "ok"
              ? "text-emerald-600"
              : item.status === "blocked"
                ? "text-destructive"
                : "text-amber-600",
          )}
        />
        <div className="min-w-0">
          <div className="break-words text-sm font-black">{item.label}</div>
          <p className="mt-1 break-words text-sm leading-6 text-muted-foreground">
            {item.detail}
          </p>
        </div>
      </div>
    </div>
  );
}
