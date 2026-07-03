import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

const variantStyles = {
  default: "bg-slate-500/15 text-slate-400 border-slate-500/30",
  success: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  warning: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  danger: "bg-rose-500/15 text-rose-400 border-rose-500/30",
  info: "bg-sky-500/15 text-sky-400 border-sky-500/30",
};

export function Badge({ children, className, variant = "default" }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

export function StateBadge({ state }: { state: string }) {
  const s = state.toLowerCase();
  let variant: BadgeProps["variant"] = "default";
  if (s === "running") variant = "success";
  else if (s === "completed") variant = "info";
  else if (s === "failed") variant = "danger";
  else if (s === "queued") variant = "warning";

  return <Badge variant={variant}>{state}</Badge>;
}
