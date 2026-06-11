import { Label, Select } from "../../../components/ui/form";
import { HelpTooltip } from "../../../components/ui/help-tooltip";

export function QueryBuilderScopeSelect({
  help,
  helpLabel,
  label,
  onChange,
  options,
  placeholder,
  value,
}: {
  help: string;
  helpLabel: string;
  label: string;
  onChange: (value: string) => void;
  options: Array<{ label: string; value: string }>;
  placeholder: string;
  value: string;
}) {
  return (
    <Label>
      <span className="inline-flex items-center gap-1.5">
        {label}
        <HelpTooltip label={helpLabel}>{help}</HelpTooltip>
      </span>
      <Select onChange={(event) => onChange(event.target.value)} value={value}>
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </Select>
    </Label>
  );
}
