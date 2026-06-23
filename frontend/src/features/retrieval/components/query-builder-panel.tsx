import { QueryBuilderFormContent } from "./query-builder-form-content";
import type {
  RetrievalQueryBuilderActions,
  RetrievalQueryBuilderOptions,
  RetrievalQueryBuilderStatus,
  RetrievalQueryBuilderValue,
} from "./query-builder-panel-types";

export type {
  RetrievalQueryBuilderActions,
  RetrievalQueryBuilderOptions,
  RetrievalQueryBuilderStatus,
  RetrievalQueryBuilderValue,
} from "./query-builder-panel-types";

export function QueryBuilderPanel({
  actions,
  options,
  status,
  value,
}: {
  actions: RetrievalQueryBuilderActions;
  options: RetrievalQueryBuilderOptions;
  status: RetrievalQueryBuilderStatus;
  value: RetrievalQueryBuilderValue;
}) {
  return (
    <form className="grid gap-3" onSubmit={actions.onSearch}>
      <QueryBuilderFormContent
        actions={actions}
        options={options}
        status={status}
        value={value}
      />
    </form>
  );
}
