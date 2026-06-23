import { Label, Select } from "../../../components/ui/form";
import type { QueryBuilderContextControlProps } from "./query-builder-context-control-types";

export function QueryBuilderFormatControl({
  actions,
  options,
  value,
}: QueryBuilderContextControlProps) {
  return (
    <Label>
      Format
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
