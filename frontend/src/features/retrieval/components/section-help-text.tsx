import type { ReactNode } from "react";

export function SectionHelpText({ children }: { children: ReactNode }) {
  return (
    <p className="break-words text-xs font-semibold leading-5 text-muted-foreground">
      {children}
    </p>
  );
}
