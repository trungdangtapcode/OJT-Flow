import {
  filterFieldLabel,
  formatFilterValue,
  type SupportedFilterField,
} from "../model/retrieval-filter-model";

export function planFilterControlNotice(
  field: SupportedFilterField,
  value: string,
) {
  return `${filterFieldLabel(field)} set to ${formatFilterValue(field, value)}. Run search to refresh evidence.`;
}
