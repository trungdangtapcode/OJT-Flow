import { Label, Select } from "../../../components/ui/form";
import { HelpTooltip } from "../../../components/ui/help-tooltip";
import type { QueryBuilderContextControlProps } from "./query-builder-context-control-types";

export function QueryBuilderTopKControl({
  actions,
  options,
  value,
}: QueryBuilderContextControlProps) {
  return (
    <Label>
      <span className="inline-flex items-center gap-1.5">
        Top K
        <HelpTooltip label="Top K help">
          Number of ranked evidence hits to return. Use more for exploration and fewer for focused review.
        </HelpTooltip>
      </span>
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
