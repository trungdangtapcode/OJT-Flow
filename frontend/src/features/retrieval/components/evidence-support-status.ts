import type { EvidenceSupportStatus } from "./evidence-interpretation-guidance-types";

export function supportStatusBadgeVariant(
  status: EvidenceSupportStatus,
): "success" | "warning" | "destructive" {
  if (status === "strong") return "success";
  if (status === "partial") return "warning";
  return "destructive";
}
