import type { ComponentProps } from "react";

import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { SearchPlanFilterField } from "./strategy-standard-types";

export type BadgeVariant = ComponentProps<typeof Badge>["variant"];

export function standardSearchMatchReasons(metadata: Record<string, unknown>) {
  const sources: {
    key: string;
    label: string;
    variant: BadgeVariant;
  }[] = [
    { key: "matched_fields", label: "field", variant: "default" },
    { key: "matched_query_aspects", label: "aspect", variant: "muted" },
    { key: "matched_standards", label: "standard", variant: "success" },
    { key: "matched_concepts", label: "concept", variant: "muted" },
    { key: "source_quality_signal_codes", label: "signal", variant: "warning" },
  ];
  return sources.flatMap((source) =>
    stringArrayValue(metadata[source.key])
      .slice(0, 3)
      .map((value) => ({
        label: source.label,
        value,
        variant: source.variant,
      })),
  );
}

export function standardRouteBadgeVariant(
  routeType: string,
): "default" | "success" | "warning" | "destructive" | "muted" {
  const normalized = routeType.toLowerCase();
  if (normalized.includes("privacy") || normalized.includes("review")) return "warning";
  if (normalized.includes("fhir") || normalized.includes("terminology")) return "default";
  if (normalized.includes("validation")) return "success";
  if (normalized.includes("external")) return "muted";
  return "muted";
}

export function strategyRecommendationVariant(status: string) {
  if (status === "active") return "success";
  if (status === "action_required" || status === "caution") return "warning";
  return "muted";
}

export function filterFieldLabel(field: SearchPlanFilterField): string {
  if (field === "clinical_domain") return "Domain";
  if (field === "source_id") return "Source ID";
  if (field === "standard_system") return "Standard";
  if (field === "source_type") return "Source";
  return "Trust";
}

export function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}

export function routeLabel(routeType: string) {
  return humanize(routeType);
}

export function stringArrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.length > 0);
}
