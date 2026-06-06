import * as React from "react";

import { Badge } from "../../../components/ui/badge";
import { Input } from "../../../components/ui/form";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import { Notice } from "../../../components/ui/notice";
import { cn, humanize } from "../../../lib/utils";
import type { RetrievalSearchPreset } from "../../../types";

export function SearchPresetStrip({
  activePresetId,
  isLoading,
  onApplyPreset,
  presets,
}: {
  activePresetId: string | null;
  isLoading: boolean;
  onApplyPreset: (preset: RetrievalSearchPreset) => void;
  presets: RetrievalSearchPreset[];
}) {
  const [categoryFilter, setCategoryFilter] = React.useState<string | null>(null);
  const [presetSearch, setPresetSearch] = React.useState("");
  const categories = uniqueValues(presets.map((preset) => preset.category));
  const filteredPresets = presets.filter((preset) => {
    if (categoryFilter && preset.category !== categoryFilter) return false;
    return presetMatchesSearch(preset, presetSearch);
  });

  if (isLoading) {
    return (
      <div className="rounded-md border border-border bg-muted/20 px-3 py-2 text-sm font-semibold text-muted-foreground">
        Loading retrieval presets
      </div>
    );
  }

  if (!presets.length) {
    return (
      <Notice title="No retrieval presets">
        Add presets under the trusted knowledge directory to seed the query builder.
      </Notice>
    );
  }

  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-muted-foreground">
          Search presets
          <HelpTooltip label="Search presets help">
            Data-driven examples loaded from trusted knowledge configuration. Applying one fills the query builder but does not run search until you submit.
          </HelpTooltip>
        </div>
        <Badge variant="muted">
          {filteredPresets.length}/{presets.length} data-driven
        </Badge>
      </div>
      <div className="grid gap-2">
        <Input
          aria-label="Filter retrieval presets"
          onChange={(event) => setPresetSearch(event.target.value)}
          placeholder="Filter presets"
          value={presetSearch}
        />
        {categories.length ? (
          <div className="flex min-w-0 flex-wrap gap-2" aria-label="Preset categories">
            <button
              aria-pressed={!categoryFilter}
              className={presetFilterClass(!categoryFilter)}
              onClick={() => setCategoryFilter(null)}
              type="button"
            >
              All
            </button>
            {categories.map((category) => {
              const active = categoryFilter === category;
              return (
                <button
                  aria-pressed={active}
                  className={presetFilterClass(active)}
                  key={category}
                  onClick={() => setCategoryFilter(category)}
                  type="button"
                >
                  {humanize(category)}
                </button>
              );
            })}
          </div>
        ) : null}
      </div>
      <div className="grid gap-2">
        {filteredPresets.length ? null : (
          <Notice title="No matching presets">
            Adjust the preset filter or category to show trusted retrieval examples.
          </Notice>
        )}
        {filteredPresets.map((preset) => {
          const active = activePresetId === preset.preset_id;
          return (
            <button
              aria-pressed={active}
              className={cn(
                "grid min-w-0 gap-1 rounded-md border px-3 py-2 text-left text-sm transition-colors",
                active
                  ? "border-primary bg-primary/10 text-foreground"
                  : "border-border bg-card hover:bg-muted",
              )}
              key={preset.preset_id}
              onClick={() => onApplyPreset(preset)}
              title={preset.description}
              type="button"
            >
              <span className="flex min-w-0 flex-wrap items-center justify-between gap-2">
                <span className="flex min-w-0 flex-wrap items-center gap-2">
                  <span className="break-words font-black">{preset.label}</span>
                  {preset.category ? (
                    <span className="rounded-full bg-muted px-2 py-1 text-xs font-bold text-muted-foreground">
                      {humanize(preset.category)}
                    </span>
                  ) : null}
                </span>
                <span className="rounded-full bg-muted px-2 py-1 text-xs font-bold text-muted-foreground">
                  top {preset.top_k}
                </span>
              </span>
              <span className="break-words text-xs leading-5 text-muted-foreground">
                {preset.description}
              </span>
              {preset.target_sources.length || preset.launch_hint_targets.length ? (
                <span className="flex min-w-0 flex-wrap gap-1 pt-1">
                  {preset.target_sources.slice(0, 3).map((source) => (
                    <span
                      className="rounded-full border border-border bg-background px-2 py-1 text-[11px] font-bold text-muted-foreground"
                      key={source}
                    >
                      {source}
                    </span>
                  ))}
                  {preset.launch_hint_targets.slice(0, 2).map((target) => (
                    <span
                      className="rounded-full border border-border bg-background px-2 py-1 text-[11px] font-bold text-muted-foreground"
                      key={target}
                    >
                      {humanize(target)}
                    </span>
                  ))}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function presetFilterClass(active: boolean) {
  return cn(
    "rounded-full border px-3 py-1 text-xs font-bold transition-colors",
    active
      ? "border-primary bg-primary/10 text-primary"
      : "border-border bg-background text-muted-foreground hover:bg-muted",
  );
}

function presetMatchesSearch(preset: RetrievalSearchPreset, search: string) {
  const normalizedSearch = search.trim().toLowerCase();
  if (!normalizedSearch) return true;

  return [
    preset.label,
    preset.description,
    preset.query,
    preset.category,
    preset.schema_id,
    preset.detected_format,
    preset.resource_type,
    preset.clinical_domain,
    preset.standard_system,
    preset.source_type,
    ...preset.fields,
    ...preset.target_sources,
    ...preset.launch_hint_targets,
  ].some((value) => value?.toLowerCase().includes(normalizedSearch));
}

function uniqueValues(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort();
}
