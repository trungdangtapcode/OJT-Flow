import type * as React from "react";

import type { RetrievalQueryColumn } from "../components/retrieval-query-column";
import { retrievalPageQueryBuilderProps } from "./retrieval-page-query-builder-props";
import type { RetrievalPagePropsArgs } from "./retrieval-page-prop-types";
import { retrievalPageSearchPlanPreviewProps } from "./retrieval-page-search-plan-preview-props";
import { retrievalPageSearchRunHistoryProps } from "./retrieval-page-search-run-history-props";

export function retrievalPageQueryColumnProps(
  args: RetrievalPagePropsArgs,
): React.ComponentProps<typeof RetrievalQueryColumn> {
  return {
    queryBuilder: retrievalPageQueryBuilderProps(args),
    searchPlanPreview: retrievalPageSearchPlanPreviewProps(args),
    searchRunHistory: retrievalPageSearchRunHistoryProps({
      searchMutation: args.searchMutation,
      workspace: args.workspace,
    }),
  };
}
