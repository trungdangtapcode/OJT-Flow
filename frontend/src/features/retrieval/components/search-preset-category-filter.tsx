import { cn, humanize } from "../../../lib/utils";

export function SearchPresetCategoryFilter({
  activeCategory,
  categories,
  onSelectCategory,
}: {
  activeCategory: string | null;
  categories: string[];
  onSelectCategory: (category: string | null) => void;
}) {
  if (!categories.length) return null;

  return (
    <div className="flex min-w-0 flex-wrap gap-2" aria-label="Preset categories">
      <button
        aria-pressed={!activeCategory}
        className={presetFilterClass(!activeCategory)}
        onClick={() => onSelectCategory(null)}
        type="button"
      >
        All
      </button>
      {categories.map((category) => {
        const active = activeCategory === category;
        return (
          <button
            aria-pressed={active}
            className={presetFilterClass(active)}
            key={category}
            onClick={() => onSelectCategory(category)}
            type="button"
          >
            {humanize(category)}
          </button>
        );
      })}
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
