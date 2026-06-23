import type * as React from "react";

export function PageHeader({
  action,
  title,
  description,
}: {
  action?: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-3 pb-1">
      <div className="flex min-w-0 items-baseline gap-3">
        <h1 className="text-xl font-bold leading-tight tracking-tight text-foreground">{title}</h1>
        <p className="hidden text-sm text-muted-foreground sm:block">{description}</p>
      </div>
      {action}
    </div>
  );
}
