import * as React from "react";

export function useHashTargetScroll(deps: React.DependencyList = []) {
  React.useEffect(() => {
    if (!window.location.hash) return;
    const targetId = decodeURIComponent(window.location.hash.slice(1));
    if (!targetId) return;
    const handle = window.setTimeout(() => {
      document.getElementById(targetId)?.scrollIntoView({
        block: "start",
        behavior: "smooth",
      });
    }, 0);
    return () => window.clearTimeout(handle);
  }, deps);
}
