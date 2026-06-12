import {
  Card,
  CardContent,
} from "../../../components/ui/card";
import { humanize } from "../../../lib/utils";
import type {
  CorpusPartitionCatalog,
  CorpusPartitionPolicy,
  RetrievalSource,
} from "../../../types";
import { SectionHelpText } from "./section-help-text";
import { SourceInventoryFilterControls } from "./source-inventory-filter-controls";
import { SourceInventoryHeader } from "./source-inventory-header";
import { SourceInventoryReadinessPanel } from "./source-inventory-readiness-panel";
import { SourceInventorySourceList } from "./source-inventory-source-list";
import { useSourceInventoryPanelState } from "./use-source-inventory-panel-state";

export function SourceInventoryPanel({
  corpusPartitions,
  isLoading,
  isPartitionCatalogLoading,
  onUseSource,
  sources,
}: {
  corpusPartitions: CorpusPartitionCatalog | null;
  isLoading: boolean;
  isPartitionCatalogLoading: boolean;
  onUseSource: (sourceId: string) => void;
  sources: RetrievalSource[];
}) {
  const {
    filteredSources,
    filterOptions,
    filters,
    hasSourceFilters,
    readiness,
    resetFilters,
    setFilters,
  } = useSourceInventoryPanelState(sources);

  return (
    <Card className="min-w-0 overflow-hidden">
      <SourceInventoryHeader
        hasSourceFilters={hasSourceFilters}
        isLoading={isLoading}
        onClearFilters={resetFilters}
        shownCount={filteredSources.length}
        sourceCount={sources.length}
      />
      <CardContent className="grid gap-3 pt-4">
        <SectionHelpText>
          Inventory filters only inspect available sources. Use source constrains retrieval to one source ID; clear exact source scope for corpus-wide coverage.
        </SectionHelpText>
        <CorpusPartitionPolicySummary
          catalog={corpusPartitions}
          isLoading={isPartitionCatalogLoading}
        />
        <SourceInventoryReadinessPanel
          hasSourceFilters={hasSourceFilters}
          readiness={readiness}
        />
        <SourceInventoryFilterControls
          filters={filters}
          options={filterOptions}
          sourceCount={sources.length}
          shownCount={filteredSources.length}
          updateFilters={setFilters}
        />
        <SourceInventorySourceList
          hasSourceFilters={hasSourceFilters}
          isLoading={isLoading}
          onUseSource={onUseSource}
          sources={filteredSources}
        />
      </CardContent>
    </Card>
  );
}

function CorpusPartitionPolicySummary({
  catalog,
  isLoading,
}: {
  catalog: CorpusPartitionCatalog | null;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="rounded-md border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
        Loading corpus partition policy.
      </div>
    );
  }
  if (!catalog?.partitions.length) {
    return (
      <div className="rounded-md border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
        No corpus partition policy is configured.
      </div>
    );
  }
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-bold">Corpus partition policy</div>
        <div className="text-xs font-bold text-muted-foreground">
          Default: {humanize(catalog.default_partition_id)}
        </div>
      </div>
      <div className="grid gap-2 md:grid-cols-3">
        {catalog.partitions.map((partition) => (
          <CorpusPartitionPolicyCard key={partition.partition_id} partition={partition} />
        ))}
      </div>
    </div>
  );
}

function CorpusPartitionPolicyCard({ partition }: { partition: CorpusPartitionPolicy }) {
  return (
    <div className="grid gap-1 rounded-md border border-border bg-card p-2 text-xs">
      <div className="font-bold">{partition.label}</div>
      <div className="text-muted-foreground">{humanize(partition.purpose)}</div>
      <div className="flex min-w-0 flex-wrap gap-1">
        <span className="rounded-full bg-muted px-2 py-0.5 font-bold text-muted-foreground">
          {humanize(partition.visibility)}
        </span>
        <span className="rounded-full bg-muted px-2 py-0.5 font-bold text-muted-foreground">
          {partition.external_provider_allowed ? "External OK" : "No external"}
        </span>
        <span className="rounded-full bg-muted px-2 py-0.5 font-bold text-muted-foreground">
          {partition.phi_allowed ? "PHI allowed" : "No PHI"}
        </span>
      </div>
    </div>
  );
}
