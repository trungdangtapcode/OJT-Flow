import * as React from "react";

const narrowViewportQuery = "(max-width: 767px)";

export function useResponsivePageSize({
  narrow = 10,
  wide = 25,
}: {
  narrow?: number;
  wide?: number;
} = {}) {
  const [isNarrow, setIsNarrow] = React.useState(() =>
    typeof window === "undefined" ? false : window.matchMedia(narrowViewportQuery).matches,
  );

  React.useEffect(() => {
    const mediaQuery = window.matchMedia(narrowViewportQuery);
    const update = () => setIsNarrow(mediaQuery.matches);

    update();
    mediaQuery.addEventListener("change", update);
    return () => mediaQuery.removeEventListener("change", update);
  }, []);

  return isNarrow ? narrow : wide;
}
