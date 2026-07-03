"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { SectionHeader } from "@/components/ui/headers";
import { ErrorState, EmptyState } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Zap, Hash, GitBranch, ChevronRight } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export default function CandidatesPage() {
  const [selected, setSelected] = useState<string | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["candidates"],
    queryFn: api.candidates,
    refetchInterval: 8000,
  });

  const selectedCandidate = data?.find((c) => c.candidate_id === selected);

  return (
    <div className="max-w-screen-2xl mx-auto">
      <SectionHeader
        title="Alpha Candidates"
        description="Candidates queued for WorldQuant BRAIN submission"
      />

      <div className="flex gap-4">
        {/* Table */}
        <div className={cn("card overflow-hidden transition-all", selected ? "flex-1" : "w-full")}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" role="table" aria-label="Candidates table">
              <thead>
                <tr className="border-b border-default bg-surface-2">
                  {["Expression", "Campaign", "Hypothesis", "Generation", "Metrics", ""].map(
                    (h) => (
                      <th
                        key={h}
                        className="px-4 py-3 text-left text-xs font-semibold text-muted uppercase tracking-wider"
                        scope="col"
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-[hsl(var(--border-subtle))]">
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} aria-hidden="true">
                      {Array.from({ length: 6 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <Skeleton className="h-3 w-full" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : isError ? (
                  <tr>
                    <td colSpan={6}>
                      <ErrorState onRetry={() => refetch()} />
                    </td>
                  </tr>
                ) : !data?.length ? (
                  <tr>
                    <td colSpan={6}>
                      <EmptyState
                        title="No candidates yet"
                        description="Alpha candidates appear here once simulations complete and are accepted."
                        icon={<Zap className="w-6 h-6" aria-hidden="true" />}
                      />
                    </td>
                  </tr>
                ) : (
                  data.map((c) => (
                    <tr
                      key={c.candidate_id}
                      className={cn(
                        "hover:bg-surface-2 transition-colors cursor-pointer",
                        selected === c.candidate_id && "bg-[hsl(245_80%_65%/0.08)]"
                      )}
                      onClick={() =>
                        setSelected(
                          selected === c.candidate_id ? null : c.candidate_id
                        )
                      }
                      aria-selected={selected === c.candidate_id}
                      role="row"
                    >
                      <td className="px-4 py-3">
                        <code className="text-xs text-[hsl(190,85%,60%)] font-mono truncate max-w-xs block">
                          {c.expression}
                        </code>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs font-mono text-muted">
                          {c.campaign_id.slice(0, 8)}…
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs font-mono text-muted">
                          {c.hypothesis_id.slice(0, 8)}…
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="info">Gen {c.generation}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1 flex-wrap">
                          {Object.entries(c.metrics)
                            .slice(0, 3)
                            .map(([k, v]) => (
                              <span
                                key={k}
                                className="text-xs font-mono text-muted"
                              >
                                {k}:{String(v).slice(0, 6)}
                              </span>
                            ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <ChevronRight
                          className={cn(
                            "w-4 h-4 text-muted transition-transform",
                            selected === c.candidate_id && "rotate-90"
                          )}
                          aria-hidden="true"
                        />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {data && (
            <div className="px-4 py-3 border-t border-default text-xs text-muted">
              {data.length} candidate{data.length !== 1 ? "s" : ""} in queue
            </div>
          )}
        </div>

        {/* Detail Drawer */}
        {selectedCandidate && (
          <div className="w-96 card p-5 shrink-0 h-fit">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-foreground">
                Candidate Detail
              </h2>
              <button
                onClick={() => setSelected(null)}
                className="text-xs text-muted hover:text-foreground transition-colors"
                aria-label="Close detail panel"
              >
                Close
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-xs text-muted mb-1">Expression</p>
                <code className="text-xs font-mono text-[hsl(190,85%,60%)] break-all block bg-surface-2 rounded-lg p-3">
                  {selectedCandidate.expression}
                </code>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface-2 rounded-lg p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Hash className="w-3 h-3 text-muted" aria-hidden="true" />
                    <p className="text-xs text-muted">Generation</p>
                  </div>
                  <p className="text-lg font-bold text-foreground">
                    {selectedCandidate.generation}
                  </p>
                </div>
                <div className="bg-surface-2 rounded-lg p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <GitBranch className="w-3 h-3 text-muted" aria-hidden="true" />
                    <p className="text-xs text-muted">Campaign</p>
                  </div>
                  <p className="text-xs font-mono text-foreground break-all">
                    {selectedCandidate.campaign_id.slice(0, 16)}…
                  </p>
                </div>
              </div>

              <div>
                <p className="text-xs text-muted mb-2">Metrics</p>
                <div className="space-y-1.5">
                  {Object.entries(selectedCandidate.metrics).map(([k, v]) => (
                    <div
                      key={k}
                      className="flex items-center justify-between py-1.5 px-3 bg-surface-2 rounded-lg"
                    >
                      <span className="text-xs font-mono text-muted">
                        {k}
                      </span>
                      <span className="text-xs font-semibold text-foreground">
                        {String(v)}
                      </span>
                    </div>
                  ))}
                  {Object.keys(selectedCandidate.metrics).length === 0 && (
                    <p className="text-xs text-muted text-center py-2">
                      No metrics recorded
                    </p>
                  )}
                </div>
              </div>

              <div>
                <p className="text-xs text-muted mb-1">Hypothesis ID</p>
                <code className="text-xs font-mono text-muted break-all">
                  {selectedCandidate.hypothesis_id}
                </code>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
