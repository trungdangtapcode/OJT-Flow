import { sourceFilterChipClass } from "./source-filter-chip-class";

export function SourceFilterChipGroup({
  activeValue,
  formatter,
  label,
  onSelect,
  values,
}: {
  activeValue: string | null;
  formatter: (value: string) => string;
  label: string;
  onSelect: (value: string | null) => void;
  values: string[];
}) {
  if (!values.length) return null;
  return (
    <div className="grid gap-1.5">
      <div className="text-xs font-bold text-muted-foreground">{label}</div>
      <div className="flex min-w-0 flex-wrap gap-1.5">
        <button
          aria-pressed={!activeValue}
          className={sourceFilterChipClass(!activeValue)}
          onClick={() => onSelect(null)}
          type="button"
        >
          All
        </button>
        {values.map((value) => {
          const active = activeValue === value;
          return (
            <button
              aria-pressed={active}
              className={sourceFilterChipClass(active)}
              key={value}
              onClick={() => onSelect(value)}
              type="button"
            >
              {formatter(value)}
            </button>
          );
        })}
      </div>
    </div>
  );
}
