import * as React from "react";

import { cn } from "../../lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      className={cn(
        "h-10 rounded-xl border border-border/60 bg-card px-3.5 text-sm shadow-xs transition-all duration-200 placeholder:text-muted-foreground/50 hover:border-muted-foreground/30 focus:border-primary focus:shadow-[0_0_0_3px_rgba(8,145,178,0.1)] focus-ring disabled:cursor-not-allowed disabled:opacity-50",
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
        "w-full min-h-40 rounded-xl border border-border/60 bg-card px-3.5 py-2.5 text-sm shadow-xs transition-all duration-200 placeholder:text-muted-foreground/50 hover:border-muted-foreground/30 focus:border-primary focus:shadow-[0_0_0_3px_rgba(8,145,178,0.1)] focus-ring disabled:cursor-not-allowed disabled:opacity-50",
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
        "h-10 rounded-xl border border-border/60 bg-card px-3 text-sm shadow-xs transition-all duration-200 hover:border-muted-foreground/30 focus:border-primary focus:shadow-[0_0_0_3px_rgba(8,145,178,0.1)] focus-ring disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
);
Select.displayName = "Select";

export function Label({ className, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={cn("grid gap-2 text-sm font-semibold text-foreground", className)} {...props} />;
}
