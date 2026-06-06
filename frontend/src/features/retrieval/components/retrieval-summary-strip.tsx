import {
  BrainCircuit,
  Database,
  Gauge,
  Network,
  ShieldCheck,
} from "lucide-react";

import { SummaryStrip, SummaryStripItem } from "../../../components/ui/summary-strip";

type SummaryTone = "default" | "success" | "warning" | "info" | "neutral";

export type RetrievalSummaryStripViewModel = {
  coverageSupporting: string;
  coverageValue: string | number;
  hitSupporting: string;
  hitValue: number;
  readinessSupporting: string;
  readinessTone: SummaryTone;
  readinessValue: string;
  rerankerEnabled: boolean;
  rerankerSupporting: string;
  sourceCount: number;
  sourcesLoading: boolean;
};

export function RetrievalSummaryStrip({ summary }: { summary: RetrievalSummaryStripViewModel }) {
  return (
    <SummaryStrip columns={5}>
      <SummaryStripItem
        icon={Database}
        label="Sources"
        loading={summary.sourcesLoading}
        supporting="Trusted retrieval inventory"
        value={summary.sourceCount}
      />
      <SummaryStripItem
        icon={Gauge}
        label="Hits"
        supporting={summary.hitSupporting}
        tone="info"
        value={summary.hitValue}
      />
      <SummaryStripItem
        icon={ShieldCheck}
        label="Readiness"
        supporting={summary.readinessSupporting}
        tone={summary.readinessTone}
        value={summary.readinessValue}
      />
      <SummaryStripItem
        icon={Network}
        label="Coverage"
        supporting={summary.coverageSupporting}
        tone="success"
        value={summary.coverageValue}
      />
      <SummaryStripItem
        icon={BrainCircuit}
        label="Reranker"
        supporting={summary.rerankerSupporting}
        tone={summary.rerankerEnabled ? "success" : "neutral"}
        value={summary.rerankerEnabled ? "on" : "off"}
      />
    </SummaryStrip>
  );
}
