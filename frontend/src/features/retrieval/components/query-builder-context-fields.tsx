import type {
  RetrievalQueryBuilderActions,
  RetrievalQueryBuilderOptions,
  RetrievalQueryBuilderValue,
} from "./query-builder-panel-types";
import {
  QueryBuilderFormatControl,
  QueryBuilderResourceControl,
  QueryBuilderSchemaControl,
  QueryBuilderTopKControl,
} from "./query-builder-context-controls";

export function QueryBuilderContextFields({
  actions,
  options,
  value,
}: {
  actions: RetrievalQueryBuilderActions;
  options: RetrievalQueryBuilderOptions;
  value: RetrievalQueryBuilderValue;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <QueryBuilderSchemaControl actions={actions} options={options} value={value} />
      <QueryBuilderTopKControl actions={actions} options={options} value={value} />
      <QueryBuilderFormatControl actions={actions} options={options} value={value} />
      <QueryBuilderResourceControl actions={actions} options={options} value={value} />
    </div>
  );
}
