"use client";

import { SectionHeader } from "@/components/ui/headers";
import { EmptyState } from "@/components/ui/states";
import { FlaskConical, Clock, CheckCircle2, XCircle, RefreshCw } from "lucide-react";
import type { SimulationRecord } from "@/lib/api";

// AWAITING_BACKEND: GET /simulations endpoint not yet implemented
// This page will display real data once the endpoint is available.

const MOCK_STATES: SimulationRecord["status"][] = [
  "running",
  "queued",
  "completed",
  "failed",
  "retrying",
];

function StatusIcon({ status }: { status: SimulationRecord["status"] }) {
  switch (status) {
    case "running":
      return <RefreshCw className="w-4 h-4 text-emerald-400 animate-spin" aria-hidden="true" />;
    case "queued":
      return <Clock className="w-4 h-4 text-amber-400" aria-hidden="true" />;
    case "completed":
      return <CheckCircle2 className="w-4 h-4 text-sky-400" aria-hidden="true" />;
    case "failed":
      return <XCircle className="w-4 h-4 text-rose-400" aria-hidden="true" />;
    case "retrying":
      return <RefreshCw className="w-4 h-4 text-purple-400" aria-hidden="true" />;
  }
}

export default function SimulationsPage() {
  return (
    <div className="max-w-screen-2xl mx-auto">
      <SectionHeader
        title="Simulation Queue"
        description="Running, queued, completed, and failed simulations"
      />

      {/* Status cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        {MOCK_STATES.map((s) => (
          <div key={s} className="card p-4">
            <div className="flex items-center gap-2 mb-2">
              <StatusIcon status={s} />
              <span className="text-xs font-medium text-muted capitalize">
                {s}
              </span>
            </div>
            <p className="text-2xl font-bold text-foreground">0</p>
          </div>
        ))}
      </div>

      {/* Awaiting backend notice */}
      <div className="card p-5 border-amber-500/30 bg-amber-500/5">
        <div className="flex items-start gap-3">
          <FlaskConical className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-amber-400">
              Awaiting Backend Implementation
            </p>
            <p className="text-xs text-muted mt-1">
              The <code className="font-mono bg-surface-2 px-1 rounded">GET /simulations</code>{" "}
              endpoint has not yet been implemented in the SYNTHRA backend. This view will
              display live simulation records — running, queued, completed, failed, and retrying
              — once the endpoint is available.
            </p>
            <div className="mt-3 space-y-1.5 text-xs font-mono text-muted">
              <p>• <code>GET /simulations</code> — list all simulations with status filter</p>
              <p>• <code>GET /simulations/{"{id}"}</code> — single simulation detail + metrics</p>
              <p>• <code>GET /simulations/{"{id}"}/logs</code> — simulation execution logs</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <EmptyState
          title="No simulations to display"
          description="Simulation records will appear once GET /simulations is implemented in the backend."
          icon={<FlaskConical className="w-6 h-6" aria-hidden="true" />}
        />
      </div>
    </div>
  );
}
