export type QueryProfileCardView = {
  complexity: string;
  description: string;
  label: string;
  profileId: string;
  retrievalMode: string;
  route: string;
  ruleIds: string[];
};

export type QueryProfileFilterEntryView = {
  applied: boolean;
  displayValue: string;
  field: string;
  label: string;
  supported: boolean;
  value: string;
};
