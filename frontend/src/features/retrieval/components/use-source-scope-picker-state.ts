import * as React from "react";

import type { RetrievalSource } from "../../../types";
import { getVisibleSourceOptions } from "./source-scope-picker-format";

export function useSourceScopePickerState(sources: RetrievalSource[]) {
  const [search, setSearch] = React.useState("");
  const visibleSources = getVisibleSourceOptions(sources, search);

  return {
    search,
    setSearch,
    visibleSources,
  };
}
