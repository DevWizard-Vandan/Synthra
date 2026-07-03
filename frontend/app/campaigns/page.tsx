"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { SectionHeader } from "@/components/ui/headers";
import { ErrorState, EmptyState } from "@/components/ui/states";
import { StateBadge } from "@/components/ui/badge";
import { TableRowSkeleton } from "@/components/ui/skeleton";
import { Layers } from "lucide-react";
import { formatNumber } from "@/lib/utils";

export default function CampaignsPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["campaigns"],
    queryFn: api.campaigns,
    refetchInterval: 15000,
  });

  return (
    <div className="max-w-screen-2xl mx-auto">
      <SectionHeader
        title="Campaigns"
        description="All research campaigns and their current states"
      />

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="table" aria-label="Campaigns table">
            <thead>
              <tr className="border-b border-default bg-surface-2">
                {[
                  "Name",
                  "Region",
                  "Universe",
                  "State",
                  "Budget",
                  "Budget Spent",
                  "Alphas Target",
                  "Max Sims",
                  "Status",
                ].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-semibold text-muted uppercase tracking-wider"
                    scope="col"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[hsl(var(--border-subtle))]">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRowSkeleton key={i} cols={9} />
                ))
              ) : isError ? (
                <tr>
                  <td colSpan={9}>
                    <ErrorState onRetry={() => refetch()} />
                  </td>
                </tr>
              ) : !data?.campaigns.length ? (
                <tr>
                  <td colSpan={9}>
                    <EmptyState
                      title="No campaigns yet"
                      description="Campaigns will appear here once they are created via the API."
                      icon={<Layers className="w-6 h-6" aria-hidden="true" />}
                    />
                  </td>
                </tr>
              ) : (
                data.campaigns.map((c) => (
                  <tr
                    key={c.id}
                    className="hover:bg-surface-2 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium text-foreground">{c.name}</div>
                      <div className="text-xs font-mono text-muted">{c.id.slice(0, 12)}…</div>
                    </td>
                    <td className="px-4 py-3 text-muted">{c.region}</td>
                    <td className="px-4 py-3 text-muted">{c.universe}</td>
                    <td className="px-4 py-3">
                      <StateBadge state={c.state} />
                    </td>
                    <td className="px-4 py-3 text-foreground font-mono">
                      ${formatNumber(c.budget_limit)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-surface-2 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="h-full bg-[hsl(245,80%,65%)] rounded-full"
                            style={{
                              width: `${Math.min(100, (c.budget_spent / c.budget_limit) * 100)}%`,
                            }}
                          />
                        </div>
                        <span className="text-xs text-muted font-mono w-14 text-right">
                          ${formatNumber(c.budget_spent)}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center text-foreground">
                      {c.target_alpha_count}
                    </td>
                    <td className="px-4 py-3 text-center text-foreground">
                      {c.max_simulations}
                    </td>
                    <td className="px-4 py-3">
                      <StateBadge state={c.status} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {data && (
          <div className="px-4 py-3 border-t border-default text-xs text-muted">
            {data.total} campaign{data.total !== 1 ? "s" : ""} total
          </div>
        )}
      </div>
    </div>
  );
}
