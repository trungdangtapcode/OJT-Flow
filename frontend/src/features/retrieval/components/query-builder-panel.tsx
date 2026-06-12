import {
  Card,
  CardContent,
} from "../../../components/ui/card";
import { QueryBuilderFormContent } from "./query-builder-form-content";
import { QueryBuilderHeader } from "./query-builder-header";
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
    <Card className="min-w-0 overflow-hidden">
      <QueryBuilderHeader />
      <CardContent className="pt-4">
        <form className="grid gap-4" onSubmit={actions.onSearch}>
          <QueryBuilderFormContent
            actions={actions}
            options={options}
            status={status}
            value={value}
          />
        </form>
      </CardContent>
    </Card>
  );
}
