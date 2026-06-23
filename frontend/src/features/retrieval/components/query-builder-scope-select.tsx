import { Label, Select } from "../../../components/ui/form";

export function QueryBuilderScopeSelect({
  label,
  onChange,
  options,
  placeholder,
  value,
}: {
  help?: string;
  helpLabel?: string;
  label: string;
  onChange: (value: string) => void;
  options: Array<{ label: string; value: string }>;
  placeholder: string;
  value: string;
}) {
  return (
    <Label>
      {label}
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
