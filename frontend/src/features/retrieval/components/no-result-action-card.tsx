import type { ReactNode } from "react";

export function NoResultActionCard({
  children,
  text,
  title,
}: {
  children?: ReactNode;
  text: string;
  title: string;
}) {
  return (
    <div className="grid content-start gap-2 rounded-md border border-amber-200 bg-card px-3 py-2">
      <div className="font-black">{title}</div>
      <p className="text-sm leading-6 text-muted-foreground">{text}</p>
      {children}
    </div>
  );
}
