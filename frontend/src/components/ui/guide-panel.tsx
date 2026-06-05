import type * as React from "react";
import { BookOpen, CheckCircle2, HelpCircle } from "lucide-react";

import { cn } from "../../lib/utils";
import { Badge } from "./badge";
import { Button } from "./button";

export function GuidePanel({
  children,
  className,
  title,
}: {
  children: React.ReactNode;
  className?: string;
  title: string;
}) {
  return (
    <details className={cn("rounded-md border border-border bg-muted/25 px-4 py-3", className)}>
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2 text-sm font-black">
        <HelpCircle className="h-4 w-4 text-primary" />
        {title}
        <Badge variant="muted">guide</Badge>
      </summary>
      <div className="mt-3">{children}</div>
    </details>
  );
}

export function GuideGrid({
  children,
  columns = "md:grid-cols-3",
}: {
  children: React.ReactNode;
  columns?: string;
}) {
  return <div className={cn("grid gap-3 text-sm leading-6", columns)}>{children}</div>;
}

export function GuideItem({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2">
      <div className="font-black">{title}</div>
      <div className="mt-1 text-muted-foreground">{children}</div>
    </div>
  );
}

export function GuideChecklist({
  items,
}: {
  items: Array<{ label: string; text: string }>;
}) {
  return (
    <ol className="grid gap-2 text-sm leading-6">
      {items.map((item) => (
        <li className="flex gap-2 rounded-md border border-border bg-card px-3 py-2" key={item.label}>
          <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-emerald-600" />
          <span>
            <span className="font-black text-foreground">{item.label}: </span>
            <span className="text-muted-foreground">{item.text}</span>
          </span>
        </li>
      ))}
    </ol>
  );
}

export function ManualLink({
  children = "Open full manual",
}: {
  children?: React.ReactNode;
}) {
  return (
    <Button asChild size="sm" type="button" variant="outline">
      <a href="/help">
        <BookOpen className="h-4 w-4" />
        {children}
      </a>
    </Button>
  );
}
