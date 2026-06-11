import {
  Card,
  CardContent,
} from "../../../components/ui/card";
import type { RetrievalSource } from "../../../types";
import { SectionHelpText } from "./section-help-text";
import { SourceInventoryFilterControls } from "./source-inventory-filter-controls";
import { SourceInventoryHeader } from "./source-inventory-header";
import { SourceInventoryReadinessPanel } from "./source-inventory-readiness-panel";
import { SourceInventorySourceList } from "./source-inventory-source-list";
import { useSourceInventoryPanelState } from "./use-source-inventory-panel-state";

export function SourceInventoryPanel({
  isLoading,
  onUseSource,
  sources,
}: {
  isLoading: boolean;
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
