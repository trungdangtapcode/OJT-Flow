import { humanize } from "../../../lib/utils";
import type { RetrievalSearchCockpitView } from "../model/retrieval-cockpit-view-model";
import { CockpitMetricCard } from "./search-cockpit-panels";
import { cockpitCountLabel, cockpitSourceCoverage } from "./search-cockpit-format";

export function SearchCockpitMetricGrid({
  view,
}: {
  view: RetrievalSearchCockpitView;
}) {
  return (
    <div className="grid gap-2 lg:grid-cols-5">
      <CockpitMetricCard
        helpText="The backend route chosen for this query, such as broad, structured, or safety-sensitive search. Use this to confirm the search behavior matches the question."
        label="Retrieval route"
        supporting={view.queryProfile ? humanize(view.queryProfile.route) : view.strategy}
        tone="info"
        value={view.queryProfile ? humanize(view.queryProfile.complexity) : "standard"}
      />
      <CockpitMetricCard
        helpText="The retrieval stack combines lexical search, vector search, and optional reranking. Stronger stacks usually improve recall and ordering, but still need evidence review."
        label="Hybrid stack"
        supporting={view.rankingSupporting}
        tone="success"
        value={view.hybridStackValue}
      />
      <CockpitMetricCard
        helpText="Whether lexical and vector retrieval agree on the same top candidates. Low agreement means inspect query wording, filters, and reranking before trusting order."
        label="Fusion agreement"
        supporting={view.fusionDiagnostics.interpretation}
        tone={view.fusionDiagnostics.tone}
        value={view.fusionDiagnostics.label}
      />
      <CockpitMetricCard
        helpText="How many independent sources survived source-diversity selection. Low spread can mean the answer depends on one source family."
        label="Evidence spread"
        supporting={
          view.diversity.enabled
            ? `${cockpitCountLabel(view.diversity.selectedSourceCount, "selected source")}`
            : "source diversity disabled"
        }
        tone={view.diversity.enabled ? "success" : "warning"}
        value={cockpitSourceCoverage(view.diversity)}
      />
      <CockpitMetricCard
        helpText="Concepts and query aspects detected from the search. Good grounding means the result matched the intended medical data concept, not just similar words."
        label="Grounding"
        supporting={cockpitCountLabel(view.queryAspectCount, "query aspect")}
        tone={view.conceptGroundingCount ? "success" : "warning"}
        value={cockpitCountLabel(view.conceptGroundingCount, "concept")}
      />
    </div>
  );
}
