"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Globe, Bot, Layers, RefreshCw } from "lucide-react";

function StatusPill({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface-2 border border-default">
      <span className="text-xs text-muted">{label}</span>
      <span className={cn("text-xs font-semibold", color ?? "text-foreground")}>
        {value}
      </span>
    </div>
  );
}

export function TopNav() {
  const { data: status, isFetching } = useQuery({
    queryKey: ["status"],
    queryFn: api.status,
    refetchInterval: 5000,
  });

  const currentCampaign =
    status?.current_campaigns?.[0] ?? "None";

  return (
    <header className="fixed top-0 left-0 right-0 h-14 bg-surface/90 border-b border-default z-40 backdrop-blur-md flex items-center px-4 gap-4">
      {/* Brand */}
      <div className="flex items-center gap-2.5 w-56 shrink-0">
        <div className="w-7 h-7 rounded-lg gradient-primary flex items-center justify-center shadow-lg glow-primary">
          <span className="text-white font-black text-sm leading-none">S</span>
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-foreground text-sm leading-tight tracking-wide">
            SYNTHRA
          </span>
          <span className="text-[10px] text-muted leading-tight">
            Operations Center
          </span>
        </div>
      </div>

      {/* Status pills */}
      <div className="flex items-center gap-2 flex-1 overflow-x-auto scrollbar-none">
        <StatusPill
          label="v"
          value={status?.version ?? "0.1.0"}
        />

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface-2 border border-default">
          <Globe className="w-3 h-3 text-muted" aria-hidden="true" />
          <span className="text-xs text-muted">WorldQuant</span>
          <span className="text-xs font-semibold text-amber-400">
            Connected
          </span>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface-2 border border-default">
          <Bot className="w-3 h-3 text-muted" aria-hidden="true" />
          <span className="text-xs text-muted">LLM</span>
          <span className="text-xs font-semibold text-sky-400">Active</span>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface-2 border border-default">
          <Layers className="w-3 h-3 text-muted" aria-hidden="true" />
          <span className="text-xs text-muted">Campaign</span>
          <span className="text-xs font-semibold text-foreground truncate max-w-28">
            {currentCampaign.slice(0, 16)}
            {currentCampaign.length > 16 ? "…" : ""}
          </span>
        </div>

        <StatusPill
          label="Workers"
          value={String(status?.active_workers ?? 0)}
          color={
            (status?.active_workers ?? 0) > 0
              ? "text-emerald-400"
              : "text-muted"
          }
        />

        <StatusPill
          label="Queue"
          value={String(
            (status?.queue_sizes?.campaign_queue ?? 0) +
              (status?.queue_sizes?.submission_queue ?? 0)
          )}
        />
      </div>

      {/* Refresh indicator */}
      <div className="shrink-0 flex items-center gap-2">
        <RefreshCw
          className={cn(
            "w-3.5 h-3.5 text-muted",
            isFetching && "animate-spin"
          )}
          aria-label={isFetching ? "Refreshing" : ""}
        />
        <div
          className={cn(
            "w-2 h-2 rounded-full",
            status ? "bg-emerald-500" : "bg-rose-500"
          )}
          aria-label={status ? "Backend connected" : "Backend offline"}
        />
      </div>
    </header>
  );
}
