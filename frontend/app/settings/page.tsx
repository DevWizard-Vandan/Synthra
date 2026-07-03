"use client";

import { SectionHeader } from "@/components/ui/headers";
import { Globe, Bot, Sliders, Cpu } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="max-w-3xl mx-auto">
      <SectionHeader
        title="Settings"
        description="Frontend configuration — backend settings are managed via environment variables"
      />

      <div className="space-y-4">
        {/* API Connection */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-4 h-4 text-[hsl(245,80%,72%)]" aria-hidden="true" />
            <h2 className="text-sm font-semibold text-foreground">Backend Connection</h2>
          </div>
          <div className="space-y-3">
            <div>
              <label htmlFor="api-url" className="block text-xs text-muted mb-1">
                API Base URL
              </label>
              <input
                id="api-url"
                type="text"
                defaultValue={process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
                readOnly
                className="w-full bg-surface-2 border border-default rounded-lg px-3 py-2 text-sm text-foreground font-mono focus:outline-none focus:border-[hsl(245,80%,65%)] transition-colors"
                aria-describedby="api-url-hint"
              />
              <p id="api-url-hint" className="text-xs text-muted mt-1">
                Set via <code className="font-mono bg-surface-2 px-1 rounded">NEXT_PUBLIC_API_URL</code> environment variable
              </p>
            </div>
          </div>
        </div>

        {/* LLM Provider — read-only reference */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Bot className="w-4 h-4 text-sky-400" aria-hidden="true" />
            <h2 className="text-sm font-semibold text-foreground">LLM Provider</h2>
          </div>
          <p className="text-xs text-muted">
            LLM provider configuration is managed in the backend via environment variables
            (<code className="font-mono bg-surface-2 px-1 rounded">LLM_PROVIDER</code>,{" "}
            <code className="font-mono bg-surface-2 px-1 rounded">OPENAI_API_KEY</code>, etc.).
            View current status in the Telemetry section.
          </p>
        </div>

        {/* WorldQuant — read-only reference */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-4 h-4 text-emerald-400" aria-hidden="true" />
            <h2 className="text-sm font-semibold text-foreground">WorldQuant BRAIN</h2>
          </div>
          <p className="text-xs text-muted">
            WorldQuant credentials are managed in the backend via environment variables
            (<code className="font-mono bg-surface-2 px-1 rounded">WQ_USERNAME</code>,{" "}
            <code className="font-mono bg-surface-2 px-1 rounded">WQ_PASSWORD</code>).
          </p>
        </div>

        {/* Campaign Defaults — AWAITING_BACKEND */}
        <div className="card p-5 border-amber-500/30 bg-amber-500/5">
          <div className="flex items-center gap-2 mb-4">
            <Sliders className="w-4 h-4 text-amber-400" aria-hidden="true" />
            <h2 className="text-sm font-semibold text-amber-400">
              Campaign Defaults — Awaiting Backend
            </h2>
          </div>
          <p className="text-xs text-muted">
            Campaign default configuration (budget, simulation concurrency, research limits)
            will be configurable here once{" "}
            <code className="font-mono bg-surface-2 px-1 rounded">GET/PUT /settings/campaigns</code>{" "}
            is implemented in the backend.
          </p>
        </div>

        {/* Simulation Concurrency — AWAITING_BACKEND */}
        <div className="card p-5 border-amber-500/30 bg-amber-500/5">
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="w-4 h-4 text-amber-400" aria-hidden="true" />
            <h2 className="text-sm font-semibold text-amber-400">
              Simulation Concurrency — Awaiting Backend
            </h2>
          </div>
          <p className="text-xs text-muted">
            Worker count and simulation concurrency settings will be configurable here once
            <code className="font-mono bg-surface-2 px-1 rounded ml-1">PUT /settings/workers</code>{" "}
            is implemented.
          </p>
        </div>
      </div>
    </div>
  );
}
