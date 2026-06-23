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
    <details className={cn("rounded-lg border border-border/40 bg-muted/15 px-3 py-2", className)}>
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2 text-xs font-semibold text-muted-foreground">
        <HelpCircle className="h-3.5 w-3.5 text-primary" />
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
    <div className="rounded-xl border border-border/50 bg-card px-4 py-3">
      <div className="font-semibold">{title}</div>
      <div className="mt-1.5 text-muted-foreground">{children}</div>
    </div>
  );
}

export function GuideChecklist({
  items,
}: {
  items: Array<{ label: string; text: string }>;
}) {
  return (
    <ol className="grid gap-2.5 text-sm leading-6">
      {items.map((item) => (
        <li className="flex gap-3 rounded-xl border border-border/50 bg-card px-4 py-3" key={item.label}>
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
          <span>
            <span className="font-semibold text-foreground">{item.label}: </span>
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
