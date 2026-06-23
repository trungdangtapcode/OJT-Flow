import { Label, Select } from "../../../components/ui/form";
import type { QueryBuilderContextControlProps } from "./query-builder-context-control-types";

export function QueryBuilderTopKControl({
  actions,
  options,
  value,
}: QueryBuilderContextControlProps) {
  return (
    <Label>
      Top K
      <Select
        onChange={(event) => actions.onSetTopK(Number(event.target.value))}
        value={value.topK}
      >
        {options.topKOptions.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </Select>
    </Label>
  );
}
