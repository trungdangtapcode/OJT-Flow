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
    description: "Mark this evidence as not relevant for the submitted query.",
    label: "Not relevant",
    value: "not_relevant",
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
  return "Not relevant";
}

export function judgmentBadgeVariant(
  value: RelevanceJudgmentValue,
): "default" | "success" | "warning" | "destructive" | "muted" {
  if (value === "relevant") return "success";
  if (value === "partial") return "warning";
  return "destructive";
}
