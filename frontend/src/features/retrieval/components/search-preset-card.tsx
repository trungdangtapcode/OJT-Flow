import { cn, humanize } from "../../../lib/utils";
import type { RetrievalSearchPreset } from "../../../types";

export function SearchPresetCard({
  active,
  onApplyPreset,
  preset,
}: {
  active: boolean;
  onApplyPreset: (preset: RetrievalSearchPreset) => void;
  preset: RetrievalSearchPreset;
}) {
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
}
