import type { RelevanceJudgmentValue } from "./retrieval-judgment-types";

export type RelevanceJudgmentOption = {
  activeVariant: "default" | "secondary" | "destructive";
  description: string;
  label: string;
  value: RelevanceJudgmentValue;
};

export const relevanceJudgmentOptions: RelevanceJudgmentOption[] = [
  {
    activeVariant: "default",
    description: "Mark this evidence as relevant for the submitted query.",
    label: "Relevant",
    value: "relevant",
  },
  {
    activeVariant: "secondary",
    description: "Mark this evidence as partially relevant for the submitted query.",
    label: "Partial",
    value: "partial",
  },
  {
    activeVariant: "destructive",
    description: "Mark this evidence as irrelevant for the submitted query.",
    label: "Irrelevant",
    value: "irrelevant",
  },
  {
    activeVariant: "destructive",
    description: "Mark this evidence as unsafe to use in the current workflow.",
    label: "Unsafe",
    value: "unsafe",
  },
  {
    activeVariant: "secondary",
    description: "Mark this evidence as stale or version-mismatched.",
    label: "Stale",
    value: "stale",
  },
  {
    activeVariant: "destructive",
    description: "Mark this evidence as blocked by source policy.",
    label: "Policy blocked",
    value: "source_policy_blocked",
  },
];

export function relevanceJudgmentRating(value: RelevanceJudgmentValue): number {
  if (value === "relevant") return 3;
  if (value === "partial") return 1;
  return 0;
}

export function judgmentLabel(value: RelevanceJudgmentValue): string {
  if (value === "relevant") return "Relevant";
  if (value === "partial") return "Partial";
  if (value === "irrelevant") return "Irrelevant";
  if (value === "unsafe") return "Unsafe";
  if (value === "stale") return "Stale";
  if (value === "source_policy_blocked") return "Policy blocked";
  return "Not relevant";
}

export function judgmentBadgeVariant(
  value: RelevanceJudgmentValue,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (value === "relevant") return "success";
  if (value === "partial") return "warning";
  if (value === "stale") return "warning";
  return "destructive";
}

export function isNonPositiveJudgment(value: RelevanceJudgmentValue): boolean {
  return (
    value === "irrelevant" ||
    value === "not_relevant" ||
    value === "unsafe" ||
    value === "stale" ||
    value === "source_policy_blocked"
  );
}
