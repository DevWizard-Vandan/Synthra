import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  trendUp?: boolean;
  iconColor?: string;
  iconBg?: string;
  className?: string;
  subtext?: string;
}

export function KpiCard({
  label,
  value,
  icon: Icon,
  trend,
  trendUp,
  iconColor = "text-[hsl(245,80%,72%)]",
  iconBg = "bg-[hsl(245_80%_65%/0.15)]",
  className,
  subtext,
}: KpiCardProps) {
  return (
    <div
      className={cn(
        "card p-5 flex flex-col gap-3 hover:border-[hsl(var(--border))] transition-all duration-200 group",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted uppercase tracking-wider">
          {label}
        </span>
        <div
          className={cn(
            "w-8 h-8 rounded-lg flex items-center justify-center transition-transform duration-200 group-hover:scale-110",
            iconBg
          )}
          aria-hidden="true"
        >
          <Icon className={cn("w-4 h-4", iconColor)} />
        </div>
      </div>

      <div className="flex items-end gap-2">
        <span className="text-2xl font-bold text-foreground tabular-nums">
          {value}
        </span>
        {trend && (
          <span
            className={cn(
              "text-xs font-medium mb-0.5",
              trendUp ? "text-emerald-400" : "text-rose-400"
            )}
          >
            {trendUp ? "↑" : "↓"} {trend}
          </span>
        )}
      </div>

      {subtext && (
        <p className="text-xs text-muted">{subtext}</p>
      )}
    </div>
  );
}
