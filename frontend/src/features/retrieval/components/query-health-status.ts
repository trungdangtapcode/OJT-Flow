import type { QueryHealthStatus } from "./search-cockpit-panel-types";

export function queryHealthBadgeVariant(
  status: QueryHealthStatus,
): "success" | "warning" | "destructive" | "muted" {
  if (status === "ok") return "success";
  if (status === "blocked") return "destructive";
  if (status === "review") return "warning";
  return "muted";
}

export function queryHealthOverallVariant(
  items: Array<{ status: QueryHealthStatus }>,
): "success" | "warning" | "destructive" | "muted" {
  if (items.some((item) => item.status === "blocked")) return "destructive";
  if (items.some((item) => item.status === "review")) return "warning";
  if (items.some((item) => item.status === "ok")) return "success";
  return "muted";
}

export function queryHealthOverallLabel(
  items: Array<{ status: QueryHealthStatus }>,
): string {
  if (items.some((item) => item.status === "blocked")) return "blocked";
  if (items.some((item) => item.status === "review")) return "review";
  if (items.some((item) => item.status === "ok")) return "healthy";
  return "unscored";
}
