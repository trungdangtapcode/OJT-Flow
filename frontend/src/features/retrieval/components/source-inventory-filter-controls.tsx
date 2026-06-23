import { Input } from "../../../components/ui/form";
import { humanize } from "../../../lib/utils";
import type {
  SourceInventoryFilterOptions,
  SourceInventoryFilters,
} from "../model/retrieval-source-inventory-model";
import { SourceFilterChipGroup } from "./source-filter-chip-group";
import { SourceInventoryFilterHeader } from "./source-inventory-filter-header";

export function SourceInventoryFilterControls({
  filters,
  options,
  sourceCount,
  shownCount,
  updateFilters,
}: {
  filters: SourceInventoryFilters;
  options: SourceInventoryFilterOptions;
  sourceCount: number;
  shownCount: number;
  updateFilters: (filters: SourceInventoryFilters) => void;
}) {
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3">
      <SourceInventoryFilterHeader sourceCount={sourceCount} shownCount={shownCount} />
      <Input
        aria-label="Filter trusted sources"
        onChange={(event) =>
          updateFilters({ ...filters, search: event.target.value })
        }
        placeholder="Filter sources by title, ID, type, domain, or standard"
        value={filters.search}
      />
      <SourceFilterChipGroup
        activeValue={filters.type}
        formatter={humanize}
        label="Source type"
        onSelect={(type) => updateFilters({ ...filters, type })}
        values={options.types}
      />
      <SourceFilterChipGroup
        activeValue={filters.domain}
        formatter={humanize}
        label="Domain"
        onSelect={(domain) => updateFilters({ ...filters, domain })}
        values={options.domains}
      />
      <SourceFilterChipGroup
        activeValue={filters.standard}
        formatter={(value) => value}
        label="Standard"
        onSelect={(standard) => updateFilters({ ...filters, standard })}
        values={options.standards}
      />
      <SourceFilterChipGroup
        activeValue={filters.partition}
        formatter={humanize}
        label="Corpus partition"
        onSelect={(partition) => updateFilters({ ...filters, partition })}
        values={options.partitions}
      />
      <SourceFilterChipGroup
        activeValue={filters.visibility}
        formatter={humanize}
        label="Visibility"
        onSelect={(visibility) => updateFilters({ ...filters, visibility })}
        values={options.visibilities}
      />
    </div>
  );
}
