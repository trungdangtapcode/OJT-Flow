import { Badge } from "../ui/badge";
import { humanize } from "../../lib/utils";

export function StatusBadge({ className, status }: { className?: string; status: string }) {
  if (status === "completed") return <Badge className={className} variant="success">{humanize(status)}</Badge>;
  if (status === "needs_human_review") return <Badge className={className} variant="warning">{humanize(status)}</Badge>;
  if (status === "failed" || status === "cancelled") {
    return <Badge className={className} variant="destructive">{humanize(status)}</Badge>;
  }
  return <Badge className={className} variant="muted">{humanize(status)}</Badge>;
}

export function SeverityBadge({ severity }: { severity: string }) {
  if (severity === "warning") return <Badge variant="warning">warning</Badge>;
  if (severity === "error" || severity === "critical") {
    return <Badge variant="destructive">{severity}</Badge>;
  }
  return <Badge variant="muted">{severity}</Badge>;
}
