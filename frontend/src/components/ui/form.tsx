import * as React from "react";

import { cn } from "../../lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      className={cn(
        "h-9 rounded-md border border-input bg-card px-3 text-sm shadow-[inset_0_1px_1px_rgba(16,24,40,0.015)] transition-colors placeholder:text-muted-foreground/70 hover:border-muted-foreground/50 focus:border-primary focus-ring disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      className={cn(
        "min-h-40 rounded-md border border-input bg-card px-3 py-2 text-sm shadow-[inset_0_1px_1px_rgba(16,24,40,0.015)] transition-colors placeholder:text-muted-foreground/70 hover:border-muted-foreground/50 focus:border-primary focus-ring disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
);
Textarea.displayName = "Textarea";

export const Select = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => (
    <select
      className={cn(
        "h-9 rounded-md border border-input bg-card px-3 text-sm shadow-[inset_0_1px_1px_rgba(16,24,40,0.015)] transition-colors hover:border-muted-foreground/50 focus:border-primary focus-ring disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
);
Select.displayName = "Select";

export function Label({ className, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={cn("grid gap-1.5 text-sm font-semibold text-foreground", className)} {...props} />;
}
