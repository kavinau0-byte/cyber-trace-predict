import * as React from "react";
import { cn } from "@/lib/utils";

const Badge = React.forwardRef<HTMLSpanElement, React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "critical" | "high" | "medium" | "success" | "outline";
}>(({ className, variant = "default", ...props }, ref) => {
  const variants: Record<string, string> = {
    default: "bg-brand/10 text-brand border-brand/20",
    critical: "bg-critical/10 text-critical border-critical/20",
    high: "bg-high/10 text-high border-high/20",
    medium: "bg-medium/10 text-medium border-medium/20",
    success: "bg-success/10 text-success border-success/20",
    outline: "bg-transparent text-gray-400 border-border",
  };
  return (
    <span
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    />
  );
});
Badge.displayName = "Badge";

export { Badge };
