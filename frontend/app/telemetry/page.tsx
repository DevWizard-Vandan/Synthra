"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { SectionHeader } from "@/components/ui/headers";
import { ErrorState, EmptyState } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Activity, AlertTriangle, Info, CheckCircle2 } from "lucide-react";

function getEventIcon(type: string) {
  const t = type.toLowerCase();
  if (t.includes("error") || t.includes("fail"))
    return <AlertTriangle className="w-3.5 h-3.5 text-rose-400" aria-hidden="true" />;
  if (t.includes("complete") || t.includes("success"))
    return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" />;
  return <Info className="w-3.5 h-3.5 text-sky-400" aria-hidden="true" />;
}

function getEventVariant(type: string): "danger" | "success" | "info" | "default" {
  const t = type.toLowerCase();
  if (t.includes("error") || t.includes("fail")) return "danger";
  if (t.includes("complete") || t.includes("success")) return "success";
  return "info";
}

export default function TelemetryPage() {
  const { data: events, isLoading, isError, refetch } = useQuery({
    queryKey: ["events"],
    queryFn: api.events,
    refetchInterval: 3000,
  });

  const { data: metrics } = useQuery({
    queryKey: ["metrics"],
    queryFn: api.metrics,
    refetchInterval: 10000,
  });

  const errorCount = events?.filter(
    (e) =>
      e.event_type.toLowerCase().includes("error") ||
      e.event_type.toLowerCase().includes("fail")
  ).length ?? 0;

  return (
    <div className="max-w-screen-2xl mx-auto">
      <SectionHeader
        title="Telemetry"
        description="Live event stream and system metrics from the SYNTHRA backend"
      />

      {/* Metrics overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="card p-4">
          <p className="text-xs text-muted">Total Events</p>
          <p className="text-2xl font-bold text-foreground mt-1">
            {isLoading ? <span className="skeleton h-7 w-16 block" /> : (events?.length ?? 0)}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-muted">Errors</p>
          <p className="text-2xl font-bold text-rose-400 mt-1">{errorCount}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-muted">Unique Types</p>
          <p className="text-2xl font-bold text-foreground mt-1">
            {new Set(events?.map((e) => e.event_type)).size}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-muted">Refresh Rate</p>
          <p className="text-2xl font-bold text-sky-400 mt-1">3s</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Event log */}
        <div className="card xl:col-span-2 overflow-hidden">
          <div className="px-5 py-4 border-b border-default flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground">
              Event Stream
            </h2>
            <div className="flex items-center gap-2">
              <span className="status-dot running" aria-hidden="true" />
              <span className="text-xs text-muted">Live</span>
            </div>
          </div>
          <div
            className="overflow-y-auto max-h-[600px]"
            role="log"
            aria-label="Event log"
            aria-live="polite"
          >
            {isLoading ? (
              <div className="p-4 space-y-3">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : isError ? (
              <ErrorState onRetry={() => refetch()} />
            ) : !events?.length ? (
              <EmptyState
                title="No events yet"
                description="Events appear here as the system runs campaigns and simulations."
                icon={<Activity className="w-6 h-6" aria-hidden="true" />}
              />
            ) : (
              <div className="divide-y divide-[hsl(var(--border-subtle))]">
                {[...events].reverse().map((evt, i) => (
                  <div
                    key={i}
                    className="px-5 py-3 hover:bg-surface-2 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      {getEventIcon(evt.event_type)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <Badge variant={getEventVariant(evt.event_type)}>
                            {evt.event_type}
                          </Badge>
                        </div>
                        <div className="space-y-0.5">
                          {Object.entries(evt)
                            .filter(([k]) => k !== "event_type")
                            .slice(0, 3)
                            .map(([k, v]) => (
                              <p key={k} className="text-xs text-muted font-mono truncate">
                                <span className="text-subtle">{k}:</span>{" "}
                                {String(v).slice(0, 80)}
                              </p>
                            ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Metrics panel */}
        <div className="card overflow-hidden">
          <div className="px-5 py-4 border-b border-default">
            <h2 className="text-sm font-semibold text-foreground">
              System Metrics
            </h2>
          </div>
          <div className="p-5">
            {!metrics ? (
              <div className="space-y-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-8 w-full" />
                ))}
              </div>
            ) : Object.keys(metrics).length === 0 ? (
              <EmptyState
                title="No metrics yet"
                description="Metrics populate once the Governor starts processing campaigns."
                icon={<Activity className="w-6 h-6" aria-hidden="true" />}
              />
            ) : (
              <div className="space-y-1.5">
                {Object.entries(metrics).map(([k, v]) => (
                  <div
                    key={k}
                    className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-surface-2 transition-colors"
                  >
                    <span className="text-xs font-mono text-muted truncate max-w-[60%]">
                      {k}
                    </span>
                    <span className="text-xs font-semibold text-foreground font-mono">
                      {typeof v === "number" ? v.toFixed(3) : String(v)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
