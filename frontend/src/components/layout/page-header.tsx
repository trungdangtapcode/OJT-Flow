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
    <div className="flex min-w-0 flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-2xl font-black leading-tight tracking-normal sm:text-[1.75rem]">{title}</h1>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  );
}
