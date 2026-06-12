import { Label, Select } from "../../../components/ui/form";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { QueryBuilderContextControlProps } from "./query-builder-context-control-types";

export function QueryBuilderFormatControl({
  actions,
  options,
  value,
}: QueryBuilderContextControlProps) {
  return (
    <Label>
      <span className="inline-flex items-center gap-1.5">
        Format
        <HelpTooltip label="Format filter help">
          Narrows search to evidence about a source data format such as CSV, JSON, Markdown, PDF text, or FHIR-like JSON.
        </HelpTooltip>
      </span>
      <Select
        onChange={(event) => actions.onSetDetectedFormat(event.target.value)}
        value={value.detectedFormat}
      >
        <option value="">Any format</option>
        {options.formatOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </Select>
    </Label>
  );
}
