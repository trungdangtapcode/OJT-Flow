import { formatSearchAnswerCount } from "./search-answer-format";

export function SearchAnswerWarningPanel({ warnings }: { warnings: string[] }) {
  if (!warnings.length) return null;
  return (
    <div className="grid gap-1 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5">
      <div className="font-black uppercase text-amber-800">
        Coverage warnings
      </div>
      {warnings.slice(0, 3).map((warning) => (
        <div className="break-words text-amber-900" key={warning}>
          {warning}
        </div>
      ))}
      {warnings.length > 3 ? (
        <div className="font-semibold text-amber-900">
          {formatSearchAnswerCount(warnings.length - 3, "additional warning")} hidden in detailed panels.
        </div>
      ) : null}
    </div>
  );
}
