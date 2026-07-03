"use client";

import { SectionHeader } from "@/components/ui/headers";
import { Dna } from "lucide-react";

// AWAITING_BACKEND: GET /evolution/lineage, GET /evolution/generations not yet implemented

export default function EvolutionPage() {
  return (
    <div className="max-w-screen-2xl mx-auto">
      <SectionHeader
        title="Evolution"
        description="Genetic lineage, selection pressure, and generation progression"
      />

      <div className="card p-5 border-amber-500/30 bg-amber-500/5 mb-6">
        <div className="flex items-start gap-3">
          <Dna className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-amber-400">
              Awaiting Backend Implementation
            </p>
            <p className="text-xs text-muted mt-1">
              Evolution endpoints have not yet been exposed in the REST API.
              This view will display genetic lineage trees, per-generation fitness distributions,
              and selection scores once the backend implements the required routes.
            </p>
            <div className="mt-3 space-y-1.5 text-xs font-mono text-muted">
              <p>• <code>GET /evolution/lineage</code> — full lineage tree</p>
              <p>• <code>GET /evolution/generations</code> — per-generation stats</p>
              <p>• <code>GET /evolution/selection</code> — selection engine scores</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {["Lineage Tree", "Generation Fitness"].map((section) => (
          <div key={section} className="card p-5 h-80 flex flex-col">
            <h2 className="text-sm font-semibold text-foreground mb-3">{section}</h2>
            <div className="flex-1 flex items-center justify-center border border-dashed border-default rounded-lg">
              <p className="text-xs text-muted">Visualization available after endpoint implementation</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
