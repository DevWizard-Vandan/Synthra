"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { SectionHeader } from "@/components/ui/headers";
import { ErrorState, EmptyState } from "@/components/ui/states";
import { CardSkeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Users2, Cpu, CheckCircle2, XCircle, Hash, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

export default function WorkersPage() {
  const {
    data: workers,
    isLoading: wLoading,
    isError: wError,
    refetch,
  } = useQuery({
    queryKey: ["workers"],
    queryFn: api.workers,
    refetchInterval: 5000,
  });

  const { data: governor } = useQuery({
    queryKey: ["governor"],
    queryFn: api.governor,
    refetchInterval: 5000,
  });

  const { data: queue } = useQuery({
    queryKey: ["queue"],
    queryFn: api.queue,
    refetchInterval: 5000,
  });

  const alive = workers?.filter((w) => w.is_alive).length ?? 0;
  const dead = (workers?.length ?? 0) - alive;

  return (
    <div className="max-w-screen-2xl mx-auto">
      <SectionHeader
        title="Workers"
        description="Active worker threads managed by the Governor"
      />

      {/* Governor card */}
      <div className="card p-5 mb-6">
        <h2 className="text-sm font-semibold text-foreground mb-4">
          Governor
        </h2>
        {!governor ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-16 skeleton rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              {
                label: "Status",
                value: governor.status,
                icon: Cpu,
                color:
                  governor.status === "running"
                    ? "text-emerald-400"
                    : "text-rose-400",
              },
              {
                label: "Worker Count",
                value: governor.worker_count,
                icon: Users2,
                color: "text-sky-400",
              },
              {
                label: "Max Retries",
                value: governor.max_retries,
                icon: Hash,
                color: "text-amber-400",
              },
              {
                label: "Initial Backoff",
                value: `${governor.initial_backoff}s`,
                icon: Clock,
                color: "text-purple-400",
              },
            ].map(({ label, value, icon: Icon, color }) => (
              <div
                key={label}
                className="flex items-center gap-3 p-3 rounded-lg bg-surface-2"
              >
                <Icon className={cn("w-5 h-5 shrink-0", color)} aria-hidden="true" />
                <div>
                  <p className="text-xs text-muted">{label}</p>
                  <p className="text-sm font-bold text-foreground capitalize">
                    {value}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        <div className="card p-4 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" aria-hidden="true" />
          <div>
            <p className="text-xs text-muted">Active Workers</p>
            <p className="text-2xl font-bold text-foreground">{alive}</p>
          </div>
        </div>
        <div className="card p-4 flex items-center gap-3">
          <XCircle className="w-5 h-5 text-rose-400 shrink-0" aria-hidden="true" />
          <div>
            <p className="text-xs text-muted">Stopped Workers</p>
            <p className="text-2xl font-bold text-foreground">{dead}</p>
          </div>
        </div>
        <div className="card p-4 flex items-center gap-3">
          <Clock className="w-5 h-5 text-amber-400 shrink-0" aria-hidden="true" />
          <div>
            <p className="text-xs text-muted">Queue Size</p>
            <p className="text-2xl font-bold text-foreground">
              {queue?.length ?? 0}
            </p>
          </div>
        </div>
      </div>

      {/* Workers grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {wLoading ? (
          Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
        ) : wError ? (
          <div className="col-span-full">
            <ErrorState onRetry={() => refetch()} />
          </div>
        ) : !workers?.length ? (
          <div className="col-span-full">
            <EmptyState
              title="No workers running"
              description="Workers start when the Governor is running and campaigns are queued."
              icon={<Users2 className="w-6 h-6" aria-hidden="true" />}
            />
          </div>
        ) : (
          workers.map((w) => (
            <div key={w.worker_id} className="card p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "status-dot",
                      w.is_alive ? "running" : "stopped"
                    )}
                    role="status"
                    aria-label={w.is_alive ? "Worker alive" : "Worker stopped"}
                  />
                  <span className="text-sm font-semibold text-foreground">
                    {w.name}
                  </span>
                </div>
                <Badge variant={w.is_alive ? "success" : "danger"}>
                  {w.is_alive ? "alive" : "stopped"}
                </Badge>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted">
                <Hash className="w-3.5 h-3.5" aria-hidden="true" />
                Worker ID: {w.worker_id}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Campaign Queue */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-foreground mb-4">
          Campaign Queue
        </h2>
        {!queue?.length ? (
          <div className="text-center py-8 text-sm text-muted">
            Campaign queue is empty
          </div>
        ) : (
          <div className="space-y-2">
            {queue.map((item, i) => (
              <div
                key={item.id}
                className="flex items-center gap-3 p-3 rounded-lg bg-surface-2"
              >
                <span className="w-6 h-6 rounded-full bg-[hsl(245_80%_65%/0.2)] flex items-center justify-center text-xs font-bold text-[hsl(245,80%,72%)]">
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">
                    {item.name}
                  </p>
                  <p className="text-xs font-mono text-muted">
                    {item.id.slice(0, 16)}…
                  </p>
                </div>
                <Badge variant="info">P{item.priority}</Badge>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
