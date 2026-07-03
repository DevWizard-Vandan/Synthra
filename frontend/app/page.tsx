"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { KpiCard } from "@/components/ui/kpi-card";
import { KpiCardSkeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/states";
import { SectionHeader } from "@/components/ui/headers";
import { formatDuration, formatNumber } from "@/lib/utils";
import {
  Activity,
  Server,
  Users,
  Clock,
  CheckCircle2,
  FlaskConical,
  Zap,
  Database,
  GitBranch,
  BarChart3,
  TrendingUp,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { CardHeader } from "@/components/ui/cards";

// Custom Recharts tooltip
function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; name: string; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface border border-default rounded-lg px-3 py-2 shadow-xl">
      {label && <p className="text-xs text-muted mb-1">{label}</p>}
      {payload.map((p, i) => (
        <p key={i} className="text-xs font-medium" style={{ color: p.color }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
}

const CHART_COLORS = [
  "hsl(245, 80%, 65%)",
  "hsl(190, 85%, 55%)",
  "hsl(158, 70%, 48%)",
  "hsl(38, 90%, 55%)",
  "hsl(355, 75%, 55%)",
];

export default function DashboardPage() {
  const {
    data: status,
    isLoading: statusLoading,
    isError: statusError,
    refetch: refetchStatus,
  } = useQuery({
    queryKey: ["status"],
    queryFn: api.status,
    refetchInterval: 5000,
  });

  const { data: metrics } = useQuery({
    queryKey: ["metrics"],
    queryFn: api.metrics,
    refetchInterval: 10000,
  });

  const { data: system } = useQuery({
    queryKey: ["system"],
    queryFn: api.system,
    refetchInterval: 10000,
  });

  const { data: governor } = useQuery({
    queryKey: ["governor"],
    queryFn: api.governor,
    refetchInterval: 10000,
  });

  if (statusError) {
    return (
      <ErrorState
        message="Cannot reach the SYNTHRA backend at the configured URL."
        onRetry={() => refetchStatus()}
      />
    );
  }

  const campaignCounts = status?.campaign_counts ?? {};
  const queueSizes = status?.queue_sizes ?? {};
  const totalQueue =
    (queueSizes.campaign_queue ?? 0) + (queueSizes.submission_queue ?? 0);

  // Build campaign state chart data
  const campaignChartData = Object.entries(campaignCounts)
    .filter(([k]) => k !== "total")
    .map(([state, count]) => ({ state: state.charAt(0).toUpperCase() + state.slice(1), count }));

  // Build queue chart data
  const queueChartData = Object.entries(queueSizes).map(([k, v]) => ({
    name: k.replace("_", " "),
    value: v,
  }));

  return (
    <div className="max-w-screen-2xl mx-auto">
      <SectionHeader
        title="Operations Dashboard"
        description={`System uptime: ${status ? formatDuration(status.uptime_seconds) : "—"}`}
      />

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 mb-8">
        {statusLoading ? (
          Array.from({ length: 10 }).map((_, i) => <KpiCardSkeleton key={i} />)
        ) : (
          <>
            <KpiCard
              label="Governor Status"
              value={status?.governor_state ?? "—"}
              icon={Server}
              iconColor={status?.governor_state === "running" ? "text-emerald-400" : "text-rose-400"}
              iconBg={status?.governor_state === "running" ? "bg-emerald-500/15" : "bg-rose-500/15"}
              subtext={`${governor?.worker_count ?? 0} worker threads`}
            />
            <KpiCard
              label="Active Workers"
              value={status?.active_workers ?? 0}
              icon={Users}
              iconColor="text-sky-400"
              iconBg="bg-sky-500/15"
              subtext={`Max retries: ${governor?.max_retries ?? 0}`}
            />
            <KpiCard
              label="Total Simulations"
              value={formatNumber(status?.simulations ?? 0)}
              icon={FlaskConical}
              iconColor="text-purple-400"
              iconBg="bg-purple-500/15"
              subtext="Lifetime executed"
            />
            <KpiCard
              label="Queue Length"
              value={totalQueue}
              icon={Clock}
              iconColor="text-amber-400"
              iconBg="bg-amber-500/15"
              subtext={`${queueSizes.campaign_queue ?? 0} campaigns, ${queueSizes.submission_queue ?? 0} subs`}
            />
            <KpiCard
              label="Candidates"
              value={status?.candidate_queue?.size ?? 0}
              icon={Zap}
              iconColor="text-[hsl(245,80%,72%)]"
              iconBg="bg-[hsl(245_80%_65%/0.15)]"
              subtext="Awaiting submission"
            />
            <KpiCard
              label="Total Campaigns"
              value={campaignCounts.total ?? 0}
              icon={GitBranch}
              iconColor="text-sky-400"
              iconBg="bg-sky-500/15"
            />
            <KpiCard
              label="Completed"
              value={campaignCounts.completed ?? 0}
              icon={CheckCircle2}
              iconColor="text-emerald-400"
              iconBg="bg-emerald-500/15"
            />
            <KpiCard
              label="Failed"
              value={campaignCounts.failed ?? 0}
              icon={Activity}
              iconColor="text-rose-400"
              iconBg="bg-rose-500/15"
            />
            <KpiCard
              label="Database"
              value={system?.database_backend?.toUpperCase() ?? "SQLite"}
              icon={Database}
              iconColor="text-teal-400"
              iconBg="bg-teal-500/15"
              subtext={`${formatNumber(system?.simulations_executed ?? 0)} records`}
            />
            <KpiCard
              label="Uptime"
              value={status ? formatDuration(status.uptime_seconds) : "—"}
              icon={TrendingUp}
              iconColor="text-[hsl(190,85%,55%)]"
              iconBg="bg-[hsl(190_85%_55%/0.15)]"
            />
          </>
        )}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 mb-8">
        {/* Campaign States */}
        <div className="card p-5">
          <CardHeader title="Campaign States" />
          {statusLoading ? (
            <div className="h-48 skeleton rounded-lg" />
          ) : campaignChartData.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-xs text-muted">
              No campaign data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={192}>
              <BarChart
                data={campaignChartData}
                margin={{ top: 0, right: 0, left: -20, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="hsl(220,14%,18%)"
                  vertical={false}
                />
                <XAxis
                  dataKey="state"
                  tick={{ fill: "hsl(220,8%,55%)", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "hsl(220,8%,55%)", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip content={<ChartTooltip />} />
                <Bar
                  dataKey="count"
                  radius={[4, 4, 0, 0]}
                  fill="hsl(245, 80%, 65%)"
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Queue Distribution */}
        <div className="card p-5">
          <CardHeader title="Queue Distribution" />
          {statusLoading ? (
            <div className="h-48 skeleton rounded-lg" />
          ) : queueChartData.every((d) => d.value === 0) ? (
            <div className="h-48 flex items-center justify-center text-xs text-muted">
              All queues empty
            </div>
          ) : (
            <div className="h-48 flex items-center gap-6">
              <ResponsiveContainer width="60%" height={192}>
                <PieChart>
                  <Pie
                    data={queueChartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    strokeWidth={2}
                    stroke="hsl(220,14%,9%)"
                  >
                    {queueChartData.map((_, index) => (
                      <Cell
                        key={index}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 flex-1">
                {queueChartData.map((item, i) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <div
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ background: CHART_COLORS[i % CHART_COLORS.length] }}
                    />
                    <span className="text-xs text-muted truncate">{item.name}</span>
                    <span className="text-xs font-semibold text-foreground ml-auto">
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* System Metrics */}
        <div className="card p-5">
          <CardHeader title="System Metrics" />
          {!metrics ? (
            <div className="h-48 skeleton rounded-lg" />
          ) : Object.keys(metrics).length === 0 ? (
            <div className="h-48 flex items-center justify-center">
              <div className="text-center">
                <BarChart3 className="w-8 h-8 text-muted mx-auto mb-2" aria-hidden="true" />
                <p className="text-xs text-muted">No metrics available yet</p>
                <p className="text-xs text-subtle mt-1">
                  Metrics populate once the Governor is running
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(metrics)
                .slice(0, 8)
                .map(([key, val]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between py-1 border-b border-subtle last:border-0"
                  >
                    <span className="text-xs text-muted font-mono">
                      {key.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs font-semibold text-foreground">
                      {String(val)}
                    </span>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>

      {/* Active Campaigns */}
      <div className="card p-5">
        <CardHeader title="Active Campaign IDs" />
        {statusLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-8 skeleton rounded-lg" />
            ))}
          </div>
        ) : !status?.current_campaigns?.length ? (
          <div className="text-center py-8 text-sm text-muted">
            No campaigns currently in queue
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {status.current_campaigns.map((id) => (
              <span
                key={id}
                className="px-3 py-1.5 rounded-lg bg-[hsl(245_80%_65%/0.12)] border border-[hsl(245_80%_65%/0.25)] text-xs font-mono text-[hsl(245,80%,72%)]"
              >
                {id}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
