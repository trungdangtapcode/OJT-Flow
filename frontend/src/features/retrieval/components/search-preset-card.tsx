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
        "min-w-0 rounded-md border px-2.5 py-1.5 text-left text-xs transition-colors",
        active
          ? "border-primary bg-primary/10"
          : "border-border/50 bg-card hover:bg-muted/50",
      )}
      onClick={() => onApplyPreset(preset)}
      title={preset.description}
      type="button"
    >
      <span className="font-semibold">{preset.label}</span>
      {preset.category ? (
        <span className="ml-1.5 text-[10px] text-muted-foreground">{humanize(preset.category)}</span>
      ) : null}
    </button>
  );
}
