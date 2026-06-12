import type * as React from "react";

import type { RetrievalPageChrome } from "../components/retrieval-page-chrome";
import type { RetrievalQueryColumn } from "../components/retrieval-query-column";
import type { RetrievalResultsColumn } from "../components/retrieval-results-column";
import { retrievalPageChromeProps } from "./retrieval-page-chrome-props";
import type { RetrievalPagePropsArgs } from "./retrieval-page-prop-types";
import { retrievalPageQueryColumnProps } from "./retrieval-page-query-column-props";
import { retrievalPageResultsColumnProps } from "./retrieval-page-results-column-props";

export function retrievalPageProps(args: RetrievalPagePropsArgs): {
  chrome: React.ComponentProps<typeof RetrievalPageChrome>;
  queryColumn: React.ComponentProps<typeof RetrievalQueryColumn>;
  resultsColumn: React.ComponentProps<typeof RetrievalResultsColumn>;
} {
  return {
    chrome: retrievalPageChromeProps(args),
    queryColumn: retrievalPageQueryColumnProps(args),
    resultsColumn: retrievalPageResultsColumnProps(args),
  };
}
