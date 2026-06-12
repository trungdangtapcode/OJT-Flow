import type {
  RetrievalQueryBuilderActions,
  RetrievalQueryBuilderOptions,
  RetrievalQueryBuilderValue,
} from "./query-builder-panel-types";

export type QueryBuilderContextControlProps = {
  actions: RetrievalQueryBuilderActions;
  options: RetrievalQueryBuilderOptions;
  value: RetrievalQueryBuilderValue;
};
