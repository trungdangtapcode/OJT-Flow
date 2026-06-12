import type { RetrievalIntegrityItem, RetrievalIntegrityReport } from "../../../types";

export type IntegrityBadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export type IntegrityPanelProps = {
  checks: RetrievalIntegrityItem[];
  formatCount: (count: number, singular: string) => string;
  formatHash: (value: string | null | undefined) => string;
  includeCorpus: boolean;
  integrityBadgeVariant: (status: string) => IntegrityBadgeVariant;
  isFetching: boolean;
  onRefresh: () => void;
  onToggleCorpus: () => void;
  report: RetrievalIntegrityReport | undefined;
};
