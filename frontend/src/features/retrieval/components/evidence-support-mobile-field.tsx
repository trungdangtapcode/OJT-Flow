import type { ReactNode } from "react";

export function EvidenceSupportMobileField({
  children,
  label,
}: {
  children: ReactNode;
  label: string;
}) {
  return (
    <div className="min-w-0 rounded-md bg-muted/45 px-2 py-1.5">
      <div className="text-[11px] font-black uppercase text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 min-w-0">{children}</div>
    </div>
  );
}
