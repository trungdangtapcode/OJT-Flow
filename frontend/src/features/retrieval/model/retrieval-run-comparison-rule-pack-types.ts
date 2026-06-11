import type { RuntimeRetrievalRulePack } from "../../../types";

export type RetrievalRulePackChange = {
  active?: RuntimeRetrievalRulePack;
  baseline?: RuntimeRetrievalRulePack;
  name: string;
  status: "added" | "removed" | "changed" | "stable";
};
